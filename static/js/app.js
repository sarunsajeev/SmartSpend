(() => {
    const shell = document.getElementById('appShell');
    const openMenu = document.querySelector('[data-sidebar-open]');
    const closeControls = document.querySelectorAll('[data-sidebar-close]');

    if (shell && openMenu) {
        const closeSidebar = () => {
            shell.classList.remove('sidebar-open');
            openMenu.setAttribute('aria-expanded', 'false');
        };

        openMenu.addEventListener('click', () => {
            const isOpen = shell.classList.toggle('sidebar-open');
            openMenu.setAttribute('aria-expanded', String(isOpen));
        });

        closeControls.forEach((control) => control.addEventListener('click', closeSidebar));
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') closeSidebar();
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                const searchInput = document.querySelector('.global-search input');
                if (searchInput) {
                    event.preventDefault();
                    searchInput.focus();
                }
            }
        });

        document.querySelectorAll('.sidebar .nav-link').forEach((link) => {
            link.addEventListener('click', () => {
                if (window.matchMedia('(max-width: 980px)').matches) closeSidebar();
            });
        });
    }

    const searchForm = document.querySelector('.global-search');
    const searchInput = searchForm?.querySelector('input');
    if (searchForm && searchInput) {
        searchForm.addEventListener('click', (event) => {
            if (event.target !== searchInput) searchInput.focus();
        });
    }

    const notificationButton = document.querySelector('[data-notifications-toggle]');
    const notificationPanel = document.querySelector('[data-notifications-panel]');
    if (notificationButton && notificationPanel) {
        const closeNotifications = () => {
            notificationPanel.hidden = true;
            notificationButton.setAttribute('aria-expanded', 'false');
        };

        notificationButton.addEventListener('click', () => {
            const isOpen = notificationPanel.hidden;
            notificationPanel.hidden = !isOpen;
            notificationButton.setAttribute('aria-expanded', String(isOpen));
        });

        document.addEventListener('click', (event) => {
            if (!event.target.closest('.notification-wrap')) closeNotifications();
        });
    }
})();
