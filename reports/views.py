from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.text import slugify

from .forms import StatementOptionsForm
from .pdf import render_statement_pdf
from .services import build_statement_data


def _statement_context(form):
    today = timezone.localdate()
    return {
        'form': form,
        'page_heading': 'Financial statements',
        'topbar_subtitle': 'Download a private PDF report from your records',
        'today': today,
        'now': timezone.localtime(),
    }


@login_required
def statement_index(request):
    form = StatementOptionsForm()
    return render(request, 'reports/index.html', _statement_context(form))


@login_required
def statement_download(request):
    form = StatementOptionsForm(request.GET)
    if not form.is_valid():
        return render(
            request,
            'reports/index.html',
            _statement_context(form),
            status=400,
        )

    data = build_statement_data(request.user, form.cleaned_data)
    pdf = render_statement_pdf(request.user, data, generated_date=timezone.localdate())
    if data.period_end:
        period_suffix = data.period_end.isoformat()
    else:
        period_suffix = 'complete-history'
    filename = slugify(f'smartspend-{data.report_scope}-{period_suffix}') or 'smartspend-statement'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response
