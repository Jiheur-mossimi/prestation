// ============================
// GESTION DES PRESTATIONS - APP.JS
// ============================

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // ============================
    // SIDEBAR TOGGLE
    // ============================
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const overlay = document.querySelector('.sidebar-overlay');

    window.toggleSidebar = function() {
        if (sidebar) {
            // On mobile, use 'active' class
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('active');
                if (overlay) {
                    overlay.classList.toggle('active');
                }
            } else {
                // On desktop, toggle class on body
                document.body.classList.toggle('sidebar-collapsed');
            }
        }
    };

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(event) {
            event.preventDefault();
            toggleSidebar();
        });
    }

    if (mobileToggle) {
        mobileToggle.addEventListener('click', function(event) {
            event.preventDefault();
            toggleSidebar();
        });
    }

    // Fermer la sidebar lors du clic sur l'overlay
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // Fermer la sidebar lors d'un clic à l'extérieur (sur desktop)
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768) {
            const isClickInside = sidebar.contains(event.target);
            const isToggleButton = sidebarToggle.contains(event.target);
            
            if (!isClickInside && !isToggleButton && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                if (overlay) {
                    overlay.classList.remove('active');
                }
            }
        }
    });

    // ============================
    // ACTIVE MENU ITEM
    // ============================
    const menuItems = document.querySelectorAll('.sidebar-menu a');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // ============================
    // USER DROPDOWN MENU
    // ============================
    const userDropdown = document.getElementById('userDropdown');
    const userDropdownMenu = document.getElementById('userDropdownMenu');

    if (userDropdown && userDropdownMenu) {
        userDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            userDropdownMenu.classList.toggle('active');
        });

        // Fermer le menu quand on clique ailleurs
        document.addEventListener('click', function(e) {
            if (!userDropdown.contains(e.target)) {
                userDropdownMenu.classList.remove('active');
            }
        });

        // Empêcher la propagation depuis le menu
        userDropdownMenu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    // ============================
    // MODALS
    // ============================
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    };

    // ============================
    // DELETE BUTTONS HANDLER
    // ============================
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            const name = this.getAttribute('data-name');
            openDeleteModal(url, name);
        });
    });

    // Fermer modal avec Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                modal.classList.remove('active');
            });
            document.body.style.overflow = 'auto';
        }
    });

    // Fermer modal en cliquant sur l'arrière-plan
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        });
    });

    // ============================
    // ALERTS DISMISS
    // ============================
    const alerts = document.querySelectorAll('.alert-dismissible .btn-close');
    alerts.forEach(alert => {
        alert.addEventListener('click', function() {
            const alertElement = this.closest('.alert');
            alertElement.style.transition = 'opacity 0.3s ease';
            alertElement.style.opacity = '0';
            setTimeout(() => {
                alertElement.remove();
            }, 300);
        });
    });

    // ============================
    // FORM VALIDATION
    // ============================
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // ============================
    // AUTO-HIDE TIMEOUT FOR ALERTS
    // ============================
    // Masquer automatiquement toutes les alertes après 5 secondes
    const allAlerts = document.querySelectorAll('.alert');
    allAlerts.forEach(alert => {
        // Ajouter la classe auto-hide pour la transition
        alert.classList.add('alert-auto-hide');
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // ============================
    // SEARCH FUNCTIONALITY
    // ============================
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const targetTable = document.querySelector(this.dataset.target);
            
            if (targetTable) {
                const rows = targetTable.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }
        });
    });

    // ============================
    // CHECKBOX SELECT ALL
    // ============================
    const selectAllCheckboxes = document.querySelectorAll('.select-all');
    selectAllCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const targetName = this.dataset.target;
            const targetCheckboxes = document.querySelectorAll(`.checkbox-${targetName}`);
            
            targetCheckboxes.forEach(cb => {
                cb.checked = this.checked;
            });
        });
    });

    // ============================
    // PHONE INPUT FORMATTING
    // ============================
    const phoneInputs = document.querySelectorAll('.phone-input');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 9) {
                value = value.substring(0, 13);
            }
            
            if (value.length > 6) {
                value = `+${value.substring(0, 3)} ${value.substring(3, 5)} ${value.substring(5, 8)} ${value.substring(8)}`;
            } else if (value.length > 3) {
                value = `+${value.substring(0, 3)} ${value.substring(3)}`;
            } else if (value.length > 0) {
                value = `+${value}`;
            }
            
            e.target.value = value;
        });
    });


    // ============================
    // FILE INPUT PREVIEW
    // ============================
    const fileInputs = document.querySelectorAll('.file-input');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const preview = document.querySelector(this.dataset.preview);
                if (preview) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    });

    // ============================
    // COUNTER ANIMATION
    // ============================
    const counters = document.querySelectorAll('.counter');
    counters.forEach(counter => {
        const target = parseInt(counter.dataset.target);
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;

        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };

        updateCounter();
    });

    // ============================
    // CHAT FUNCTIONALITY
    // ============================
    const chatInput = document.querySelector('.chat-input');
    const chatSendBtn = document.querySelector('.chat-send-btn');
    const chatMessages = document.querySelector('.chat-messages');

    if (chatSendBtn && chatInput) {
        const sendMessage = () => {
            const message = chatInput.value.trim();
            if (message) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'chat-message sent';
                messageDiv.innerHTML = `
                    <div class="chat-message-content">
                        <div class="chat-message-bubble">
                            <p class="chat-message-text">${message}</p>
                        </div>
                        <div class="chat-message-time">${new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute:'2-digit'})}</div>
                    </div>
                `;
                
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                chatInput.value = '';
            }
        };

        chatSendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // DataTables désactivé pour éviter les erreurs
    // Les tableaux s'affichent en HTML simple

    // ============================
    // APEXCHARTS INITIALIZATION
    // ============================
    if (typeof ApexCharts !== 'undefined') {
        // Line Chart
        const lineChartEl = document.querySelector('#lineChart');
        if (lineChartEl) {
            const lineChart = new ApexCharts(lineChartEl, {
                series: [{
                    name: 'Prestations',
                    data: [30, 40, 35, 50, 49, 60, 70, 91, 125]
                }],
                chart: {
                    type: 'area',
                    height: 350,
                    toolbar: { show: false }
                },
                colors: ['#3b82f6'],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.7,
                        opacityTo: 0.2,
                        stops: [0, 90, 100]
                    }
                },
                xaxis: {
                    categories: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep']
                },
                stroke: {
                    curve: 'smooth',
                    width: 2
                },
                grid: {
                    borderColor: '#e2e8f0',
                    strokeDashArray: 4
                }
            });
            lineChart.render();
        }

        // Donut Chart
        const donutChartEl = document.querySelector('#donutChart');
        if (donutChartEl) {
            const donutChart = new ApexCharts(donutChartEl, {
                series: [44, 55, 13, 33],
                chart: {
                    type: 'donut',
                    height: 350
                },
                labels: ['Enseignants', 'Administratif', 'Discipline', 'Surveillants'],
                colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
                legend: {
                    position: 'bottom'
                },
                plotOptions: {
                    pie: {
                        donut: {
                            size: '70%'
                        }
                    }
                }
            });
            donutChart.render();
        }
    }

    // ============================
    // TIMER FOR LIVE PRESTATIONS
    // ============================
    const startTimers = document.querySelectorAll('.start-timer');
    startTimers.forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.prestation-card');
            const timeEl = card.querySelector('.time-elapsed');
            const startTime = new Date();
            
            setInterval(() => {
                const currentTime = new Date();
                const diff = currentTime - startTime;
                const hours = Math.floor(diff / 3600000);
                const minutes = Math.floor((diff % 3600000) / 60000);
                const seconds = Math.floor((diff % 60000) / 1000);
                
                timeEl.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }, 1000);
        });
    });

    // ============================
    // SMOOTH SCROLL
    // ============================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // ============================
    // TOOLTIP INITIALIZATION
    // ============================
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        if (typeof bootstrap !== 'undefined') {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        }
    });

    // ============================
    // PRINT FUNCTIONALITY
    // ============================
    window.printPage = function() {
        window.print();
    };

    // ============================
    // EXPORT EXCEL
    // ============================
    window.exportToExcel = function(tableId) {
        const table = document.getElementById(tableId);
        if (!table) return;

        let csv = [];
        const rows = table.querySelectorAll('tr');

        for (let i = 0; i < rows.length; i++) {
            let row = [];
            const cols = rows[i].querySelectorAll('td, th');

            for (let j = 0; j < cols.length; j++) {
                row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
            }

            csv.push(row.join(';'));
        }

        const csvContent = '\ufeff' + csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', 'export.csv');
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // ============================
    // EXPORT PDF
    // ============================
    window.exportToPDF = function() {
        alert('La fonctionnalité d\'export PDF sera implémentée avec une bibliothèque appropriée.');
    };

    // ============================
    // BADGE UPDATES
    // ============================
    const updateNotificationBadge = function(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    };

    // ============================
    // AUTO COMPLETE
    // ============================
    const autocompleteInputs = document.querySelectorAll('.autocomplete');
    autocompleteInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value.toLowerCase();
            const datalist = document.getElementById(this.dataset.list);
            
            if (datalist) {
                const options = datalist.querySelectorAll('option');
                options.forEach(option => {
                    const text = option.textContent.toLowerCase();
                    option.style.display = text.includes(value) ? '' : 'none';
                });
            }
        });
    });

    // ============================
    // LOADING SPINNER
    // ============================
    window.showLoading = function(element) {
        const el = document.querySelector(element);
        if (el) {
            el.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
        }
    };

    window.hideLoading = function(element, content) {
        const el = document.querySelector(element);
        if (el) {
            el.innerHTML = content;
        }
    };

    // ============================
    // CONFIRM DIALOG
    // ============================
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    };

    // ============================
    // CONFIRM SUBMIT MODAL
    // ============================
    window.confirmSubmit = function(event, title, message, details) {
        event.preventDefault();
        const form = event.target;
        const modalId = 'confirmSubmitModal';

        // Créer ou récupérer le modal
        let modal = document.getElementById(modalId);
        if (!modal) {
            modal = document.createElement('div');
            modal.id = modalId;
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h5><i class="bi bi-question-circle text-primary me-2"></i><span id="confirmTitle"></span></h5>
                        <button type="button" class="btn" onclick="closeModal('${modalId}')"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="modal-body">
                        <p id="confirmMessage"></p>
                        <p id="confirmDetails" class="text-muted small" style="display:none;">
                            <i class="bi bi-info-circle me-1"></i><span id="confirmDetailsText"></span>
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="closeModal('${modalId}')">
                            <i class="bi bi-arrow-left me-2"></i>Annuler
                        </button>
                        <button type="button" class="btn btn-primary" id="confirmSubmitBtn">
                            <i class="bi bi-check-circle me-2"></i>Confirmer
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Fermer avec Escape
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    closeModal(modalId);
                }
            });

            // Fermer en cliquant sur l'overlay
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    closeModal(modalId);
                }
            });
        }

        // Mettre à jour le contenu
        document.getElementById('confirmTitle').textContent = title || 'Confirmer l\'action';
        document.getElementById('confirmMessage').textContent = message || 'Êtes-vous sûr de vouloir effectuer cette action ?';
        
        const detailsEl = document.getElementById('confirmDetails');
        const detailsTextEl = document.getElementById('confirmDetailsText');
        if (details) {
            detailsTextEl.textContent = details;
            detailsEl.style.display = 'block';
        } else {
            detailsEl.style.display = 'none';
        }

        // Stocker le formulaire pour soumission
        window._pendingForm = form;

        // Remplacer le bouton de confirmation
        const confirmBtn = document.getElementById('confirmSubmitBtn');
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        newConfirmBtn.addEventListener('click', function() {
            if (window._pendingForm) {
                window._pendingForm.submit();
                window._pendingForm = null;
            }
            closeModal(modalId);
        });

        // Afficher le modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    };

    // Intercepter les formulaires avec data-confirm
    document.querySelectorAll('form[data-confirm]').forEach(function(form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            const title = form.getAttribute('data-confirm-title') || 'Confirmer';
            const message = form.getAttribute('data-confirm-message') || 'Êtes-vous sûr de vouloir effectuer cette action ?';
            const details = form.getAttribute('data-confirm-details') || '';
            
            // Afficher le modal de confirmation
            const modalId = 'confirmSubmitModal';
            let modal = document.getElementById(modalId);
            if (!modal) {
                // Créer le modal si nécessaire (sera fait dans confirmSubmit mock)
                window.confirmSubmit(event, title, message, details);
                return;
            }
            
            document.getElementById('confirmTitle').textContent = title;
            document.getElementById('confirmMessage').textContent = message;
            
            const detailsEl = document.getElementById('confirmDetails');
            const detailsTextEl = document.getElementById('confirmDetailsText');
            if (details) {
                detailsTextEl.textContent = details;
                detailsEl.style.display = 'block';
            } else {
                detailsEl.style.display = 'none';
            }

            window._pendingForm = form;

            const confirmBtn = document.getElementById('confirmSubmitBtn');
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            newConfirmBtn.addEventListener('click', function() {
                if (window._pendingForm) {
                    window._pendingForm.submit();
                    window._pendingForm = null;
                }
                closeModal(modalId);
            });

            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });

    // ============================
    // AJAX FORM SUBMISSION
    // ============================
    const ajaxForms = document.querySelectorAll('.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const url = this.action;
            const method = this.method;
            
            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    console.error(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });

    console.log('Application initialized successfully!');
});