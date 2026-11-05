document.addEventListener('DOMContentLoaded', () => {
    const periodField = document.querySelector('[name="period"]');
    if (!periodField) return;

    const yearRow = document.querySelector('[data-report-field="year"]');
    const monthRow = document.querySelector('[data-report-field="month"]');
    const fromRow = document.querySelector('[data-report-field="date_from"]');
    const toRow = document.querySelector('[data-report-field="date_to"]');

    const syncPeriodFields = () => {
        const period = periodField.value;
        if (yearRow) yearRow.hidden = !['monthly', 'yearly'].includes(period);
        if (monthRow) monthRow.hidden = period !== 'monthly';
        if (fromRow) fromRow.hidden = period !== 'custom';
        if (toRow) toRow.hidden = period !== 'custom';
    };

    periodField.addEventListener('change', syncPeriodFields);
    syncPeriodFields();
});
