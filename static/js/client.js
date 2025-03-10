// API Base URL
const API_BASE_URL = '/api';

// Auth Functions
async function login(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error al iniciar sesión');
        }
        
        // Store token and user info
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('userName', data.user.name);
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}

async function register(name, email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error al registrarse');
        }
        
        return true;
    } catch (error) {
        console.error('Register error:', error);
        throw error;
    }
}

async function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userName');
    window.location.href = '/login';
}

// API Helper Functions
async function fetchApi(endpoint, method = 'GET', data = null) {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    const options = {
        method,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/${endpoint}`, options);
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.error || 'Error en la solicitud');
        }
        
        return responseData;
    } catch (error) {
        console.error(`API error (${endpoint}):`, error);
        
        // Si es un error de autenticación, redirigir al login
        if (error.message.includes('Token') || error.message.includes('token')) {
            logout();
        }
        
        throw error;
    }
}

// Check Authentication
function checkAuth() {
    const token = localStorage.getItem('authToken');
    const userName = localStorage.getItem('userName');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    // Update user name in sidebar
    const userNameElement = document.getElementById('user-name');
    if (userNameElement && userName) {
        userNameElement.textContent = userName;
    }
}

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.section');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetSection = item.getAttribute('data-section');
            
            // Update active class on nav items
            navItems.forEach(ni => ni.classList.remove('active'));
            item.classList.add('active');
            
            // Update active class on sections
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === targetSection) {
                    section.classList.add('active');
                }
            });
        });
    });
}

// Modal Functions
function setupModals() {
    // Customer Modal
    setupModal('add-customer-btn', 'customer-modal');
    
    // Contact Modal
    setupModal('add-contact-btn', 'contact-modal');
    
    // Deal Modal
    setupModal('add-deal-btn', 'deal-modal');
    
    // Task Modal
    setupModal('add-task-btn', 'task-modal');
}

function setupModal(triggerButtonId, modalId) {
    const triggerButton = document.getElementById(triggerButtonId);
    const modal = document.getElementById(modalId);
    
    if (!triggerButton || !modal) return;
    
    const closeButton = modal.querySelector('.close-btn');
    
    triggerButton.addEventListener('click', () => {
        modal.style.display = 'block';
    });
    
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Customers Functions
async function loadCustomers() {
    try {
        const customers = await fetchApi('customers');
        const tableBody = document.getElementById('customers-table-body');
        
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (customers.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No hay clientes. ¡Añade tu primer cliente!</td></tr>';
            return;
        }
        
        customers.forEach(customer => {
            let statusText = '';
            switch(customer.status) {
                case 'new': statusText = 'Nuevo'; break;
                case 'contacted': statusText = 'Contactado'; break;
                case 'qualified': statusText = 'Calificado'; break;
                default: statusText = customer.status;
            }
            
            const row = `
                <tr data-id="${customer.id}">
                    <td>${customer.name}</td>
                    <td>${customer.company}</td>
                    <td>${customer.email}</td>
                    <td>${customer.phone || '-'}</td>
                    <td>${statusText}</td>
                    <td>
                        <button class="btn btn-small edit-customer">Editar</button>
                        <button class="btn btn-small btn-danger delete-customer">Eliminar</button>
                    </td>
                </tr>
            `;
            
            tableBody.innerHTML += row;
        });
        
        // Add event listeners to edit/delete buttons
        setupCustomerActions();
        
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

function setupCustomerActions() {
    // Edit customer
    document.querySelectorAll('.edit-customer').forEach(button => {
        button.addEventListener('click', async () => {
            const row = button.closest('tr');
            const customerId = row.getAttribute('data-id');
            
            // Here you would load customer data and open the edit modal
            // For simplicity, let's just alert
            alert(`Editar cliente ID: ${customerId}`);
        });
    });
    
    // Delete customer
    document.querySelectorAll('.delete-customer').forEach(button => {
        button.addEventListener('click', async () => {
            const row = button.closest('tr');
            const customerId = row.getAttribute('data-id');
            
            if (confirm('¿Estás seguro de que deseas eliminar este cliente?')) {
                try {
                    await fetchApi(`customers/${customerId}`, 'DELETE');
                    await loadCustomers(); // Reload the list
                } catch (error) {
                    console.error('Error deleting customer:', error);
                }
            }
        });
    });
}

// Setup customer form
function setupCustomerForm() {
    const form = document.getElementById('customer-form');
    
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            name: document.getElementById('customer-name').value,
            company: document.getElementById('customer-company').value,
            email: document.getElementById('customer-email').value,
            phone: document.getElementById('customer-phone').value,
            status: document.getElementById('customer-status').value,
            notes: document.getElementById('customer-notes').value
        };
        
        try {
            await fetchApi('customers', 'POST', data);
            
            // Close modal and reset form
            document.getElementById('customer-modal').style.display = 'none';
            form.reset();
            
            // Reload customers
            await loadCustomers();
            
        } catch (error) {
            console.error('Error saving customer:', error);
            alert('Error al guardar el cliente: ' + error.message);
        }
    });
}

// Contacts Functions
async function loadContacts() {
    try {
        const contacts = await fetchApi('contacts');
        const tableBody = document.querySelector('#contacts .table-container tbody');
        
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (contacts.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No hay contactos. ¡Añade tu primer contacto!</td></tr>';
            return;
        }
        
        contacts.forEach(contact => {
            const row = `
                <tr data-id="${contact.id}">
                    <td>${contact.name}</td>
                    <td>${contact.customer_name}</td>
                    <td>${contact.email}</td>
                    <td>${contact.phone || '-'}</td>
                    <td>${contact.position || '-'}</td>
                    <td>
                        <button class="btn btn-small edit-contact">Editar</button>
                        <button class="btn btn-small btn-danger delete-contact">Eliminar</button>
                    </td>
                </tr>
            `;
            
            tableBody.innerHTML += row;
        });
        
        // Setup contact actions
        setupContactActions();
        
    } catch (error) {
        console.error('Error loading contacts:', error);
    }
}

function setupContactActions() {
    // Similar to customer actions
    document.querySelectorAll('.edit-contact').forEach(button => {
        button.addEventListener('click', () => {
            const row = button.closest('tr');
            const contactId = row.getAttribute('data-id');
            alert(`Editar contacto ID: ${contactId}`);
        });
    });
    
    document.querySelectorAll('.delete-contact').forEach(button => {
        button.addEventListener('click', async () => {
            const row = button.closest('tr');
            const contactId = row.getAttribute('data-id');
            
            if (confirm('¿Estás seguro de que deseas eliminar este contacto?')) {
                try {
                    await fetchApi(`contacts/${contactId}`, 'DELETE');
                    await loadContacts();
                } catch (error) {
                    console.error('Error deleting contact:', error);
                }
            }
        });
    });
}

// Setup contact form
async function setupContactForm() {
    const form = document.getElementById('contact-form');
    const customerSelect = document.getElementById('contact-customer');
    
    if (!form || !customerSelect) return;
    
    // Load customers for the dropdown
    try {
        const customers = await fetchApi('customers');
        
        customerSelect.innerHTML = '<option value="">Seleccionar cliente...</option>';
        
        customers.forEach(customer => {
            const option = `<option value="${customer.id}">${customer.name} (${customer.company})</option>`;
            customerSelect.innerHTML += option;
        });
    } catch (error) {
        console.error('Error loading customers for contact form:', error);
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            name: document.getElementById('contact-name').value,
            customer_id: document.getElementById('contact-customer').value,
            email: document.getElementById('contact-email').value,
            phone: document.getElementById('contact-phone').value,
            position: document.getElementById('contact-position').value,
            notes: document.getElementById('contact-notes').value
        };
        
        try {
            await fetchApi('contacts', 'POST', data);
            
            // Close modal and reset form
            document.getElementById('contact-modal').style.display = 'none';
            form.reset();
            
            // Reload contacts
            await loadContacts();
            
        } catch (error) {
            console.error('Error saving contact:', error);
            alert('Error al guardar el contacto: ' + error.message);
        }
    });
}

// Deals Functions
async function loadDeals() {
    try {
        const deals = await fetchApi('deals');
        const tableBody = document.querySelector('#deals .table-container tbody');
        
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (deals.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No hay oportunidades. ¡Añade tu primera oportunidad!</td></tr>';
            return;
        }
        
        deals.forEach(deal => {
            let stageText = '';
            switch(deal.stage) {
                case 'prospect': stageText = 'Prospecto'; break;
                case 'negotiation': stageText = 'Negociación'; break;
                case 'proposal': stageText = 'Propuesta'; break;
                case 'won': stageText = 'Ganada'; break;
                case 'lost': stageText = 'Perdida'; break;
                default: stageText = deal.stage;
            }
            
            const row = `
                <tr data-id="${deal.id}">
                    <td>${deal.title}</td>
                    <td>${deal.customer_name}</td>
                    <td>$${deal.value.toFixed(2)}</td>
                    <td>${stageText}</td>
                    <td>${deal.close_date || '-'}</td>
                    <td>
                        <button class="btn btn-small edit-deal">Editar</button>
                        <button class="btn btn-small btn-danger delete-deal">Eliminar</button>
                    </td>
                </tr>
            `;
            
            tableBody.innerHTML += row;
        });
        
        // Setup deal actions
        setupDealActions();
        
    } catch (error) {
        console.error('Error loading deals:', error);
    }
}

function setupDealActions() {
    // Similar to customer/contact actions
    document.querySelectorAll('.edit-deal').forEach(button => {
        button.addEventListener('click', () => {
            const row = button.closest('tr');
            const dealId = row.getAttribute('data-id');
            alert(`Editar oportunidad ID: ${dealId}`);
        });
    });
    
    document.querySelectorAll('.delete-deal').forEach(button => {
        button.addEventListener('click', async () => {
            const row = button.closest('tr');
            const dealId = row.getAttribute('data-id');
            
            if (confirm('¿Estás seguro de que deseas eliminar esta oportunidad?')) {
                try {
                    await fetchApi(`deals/${dealId}`, 'DELETE');
                    await loadDeals();
                } catch (error) {
                    console.error('Error deleting deal:', error);
                }
            }
        });
    });
}

// Setup deal form
async function setupDealForm() {
    const form = document.getElementById('deal-form');
    const customerSelect = document.getElementById('deal-customer');
    
    if (!form || !customerSelect) return;
    
    // Load customers for the dropdown
    try {
        const customers = await fetchApi('customers');
        
        customerSelect.innerHTML = '<option value="">Seleccionar cliente...</option>';
        
        customers.forEach(customer => {
            const option = `<option value="${customer.id}">${customer.name} (${customer.company})</option>`;
            customerSelect.innerHTML += option;
        });
    } catch (error) {
        console.error('Error loading customers for deal form:', error);
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            title: document.getElementById('deal-title').value,
            customer_id: document.getElementById('deal-customer').value,
            value: parseFloat(document.getElementById('deal-value').value),
            stage: document.getElementById('deal-stage').value,
            close_date: document.getElementById('deal-close-date').value,
            notes: document.getElementById('deal-notes').value
        };
        
        try {
            await fetchApi('deals', 'POST', data);
            
            // Close modal and reset form
            document.getElementById('deal-modal').style.display = 'none';
            form.reset();
            
            // Reload deals
            await loadDeals();
            
        } catch (error) {
            console.error('Error saving deal:', error);
            alert('Error al guardar la oportunidad: ' + error.message);
        }
    });
}

// Tasks Functions
async function loadTasks() {
    try {
        const tasks = await fetchApi('tasks');
        const tableBody = document.querySelector('#tasks .table-container tbody');
        
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        if (tasks.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No hay tareas. ¡Añade tu primera tarea!</td></tr>';
            return;
        }
        
        tasks.forEach(task => {
            let priorityText = '';
            switch(task.priority) {
                case 'low': priorityText = 'Baja'; break;
                case 'medium': priorityText = 'Media'; break;
                case 'high': priorityText = 'Alta'; break;
                default: priorityText = task.priority;
            }
            
            let statusText = '';
            switch(task.status) {
                case 'pending': statusText = 'Pendiente'; break;
                case 'in_progress': statusText = 'En Progreso'; break;
                case 'completed': statusText = 'Completada'; break;
                default: statusText = task.status;
            }
            
            const relatedText = task.related_name ? `${task.related_name}` : 'General';
            
            const row = `
                <tr data-id="${task.id}">
                    <td>${task.title}</td>
                    <td>${relatedText}</td>
                    <td>${task.due_date}</td>
                    <td>${priorityText}</td>
                    <td>${statusText}</td>
                    <td>
                        <button class="btn btn-small edit-task">Editar</button>
                        <button class="btn btn-small btn-danger delete-task">Eliminar</button>
                    </td>
                </tr>
            `;
            
            tableBody.innerHTML += row;
        });
        
        // Setup task actions
        setupTaskActions();
        
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function setupTaskActions() {
    // Similar to other entity actions
    document.querySelectorAll('.edit-task').forEach(button => {
        button.addEventListener('click', () => {
            const row = button.closest('tr');
            const taskId = row.getAttribute('data-id');
            alert(`Editar tarea ID: ${taskId}`);
        });
    });
    
    document.querySelectorAll('.delete-task').forEach(button => {
        button.addEventListener('click', async () => {
            const row = button.closest('tr');
            const taskId = row.getAttribute('data-id');
            
            if (confirm('¿Estás seguro de que deseas eliminar esta tarea?')) {
                try {
                    await fetchApi(`tasks/${taskId}`, 'DELETE');
                    await loadTasks();
                } catch (error) {
                    console.error('Error deleting task:', error);
                }
            }
        });
    });
}

// Setup task form
async function setupTaskForm() {
    const form = document.getElementById('task-form');
    const relatedTypeSelect = document.getElementById('task-related-type');
    const relatedIdSelect = document.getElementById('task-related-id');
    
    if (!form || !relatedTypeSelect || !relatedIdSelect) return;
    
    // Set today as the minimum date for due date
    const dueDateInput = document.getElementById('task-due-date');
    if (dueDateInput) {
        const today = new Date().toISOString().split('T')[0];
        dueDateInput.min = today;
        dueDateInput.value = today;
    }
    
    // Update related ID options when related type changes
    relatedTypeSelect.addEventListener('change', async () => {
        const relatedType = relatedTypeSelect.value;
        
        relatedIdSelect.innerHTML = '<option value="">Seleccionar...</option>';
        
        if (!relatedType) return; // If general task, no need to load anything
        
        try {
            let items = [];
            
            if (relatedType === 'customer') {
                items = await fetchApi('customers');
                
                items.forEach(item => {
                    const option = `<option value="${item.id}">${item.name} (${item.company})</option>`;
                    relatedIdSelect.innerHTML += option;
                });
            } else if (relatedType === 'contact') {
                items = await fetchApi('contacts');
                
                items.forEach(item => {
                    const option = `<option value="${item.id}">${item.name} (${item.customer_name})</option>`;
                    relatedIdSelect.innerHTML += option;
                });
            } else if (relatedType === 'deal') {
                items = await fetchApi('deals');
                
                items.forEach(item => {
                    const option = `<option value="${item.id}">${item.title} (${item.customer_name})</option>`;
                    relatedIdSelect.innerHTML += option;
                });
            }
        } catch (error) {
            console.error(`Error loading ${relatedType} for task form:`, error);
        }
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            title: document.getElementById('task-title').value,
            related_type: document.getElementById('task-related-type').value,
            related_id: document.getElementById('task-related-id').value,
            due_date: document.getElementById('task-due-date').value,
            priority: document.getElementById('task-priority').value,
            status: document.getElementById('task-status').value,
            description: document.getElementById('task-description').value
        };
        
        try {
            await fetchApi('tasks', 'POST', data);
            
            // Close modal and reset form
            document.getElementById('task-modal').style.display = 'none';
            form.reset();
            
            // Reload tasks
            await loadTasks();
            
        } catch (error) {
            console.error('Error saving task:', error);
            alert('Error al guardar la tarea: ' + error.message);
        }
    });
}

// Dashboard Functions
async function loadDashboard() {
    try {
        const data = await fetchApi('dashboard');
        
        // Update dashboard cards
        document.querySelector('.card:nth-child(1) .card-value').textContent = data.customer_count;
        document.querySelector('.card:nth-child(2) .card-value').textContent = data.open_deals;
        document.querySelector('.card:nth-child(3) .card-value').textContent = `$${data.month_revenue.toFixed(2)}`;
        document.querySelector('.card:nth-child(4) .card-value').textContent = data.pending_tasks;
        
        // Update recent activities
        const activityList = document.querySelector('.activity-list');
        
        if (activityList) {
            activityList.innerHTML = '';
            
            if (data.recent_activities.length === 0) {
                activityList.innerHTML = `
                    <li class="activity-item">
                        <div class="activity-icon">👋</div>
                        <div>
                            <p>¡Bienvenido a tu CRM! Comienza añadiendo clientes.</p>
                            <p class="activity-time">Ahora</p>
                        </div>
                    </li>
                `;
                return;
            }
            
            data.recent_activities.forEach(activity => {
                let icon = '📝';
                
                if (activity.type === 'customer') {
                    icon = '👥';
                } else if (activity.type === 'deal') {
                    icon = '💰';
                } else if (activity.type === 'task') {
                    icon = '✅';
                } else if (activity.type === 'contact') {
                    icon = '📞';
                }
                
                const activityDate = new Date(activity.time);
                const timeAgo = formatTimeAgo(activityDate);
                
                const activityItem = `
                    <li class="activity-item">
                        <div class="activity-icon">${icon}</div>
                        <div>
                            <p>${activity.message}</p>
                            <p class="activity-time">${timeAgo}</p>
                        </div>
                    </li>
                `;
                
                activityList.innerHTML += activityItem;
            });
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Format relative time
function formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
        return 'Hace un momento';
    } else if (diffMin < 60) {
        return `Hace ${diffMin} ${diffMin === 1 ? 'minuto' : 'minutos'}`;
    } else if (diffHour < 24) {
        return `Hace ${diffHour} ${diffHour === 1 ? 'hora' : 'horas'}`;
    } else if (diffDay < 30) {
        return `Hace ${diffDay} ${diffDay === 1 ? 'día' : 'días'}`;
    } else {
        return date.toLocaleDateString();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    const currentPath = window.location.pathname;
    
    if (currentPath === '/login') {
        // Login page - no need to check auth
        return;
    }
    
    // Check authentication
    checkAuth();
    
    // Setup logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Setup navigation
    setupNavigation();
    
    // Setup modals
    setupModals();
    
    // Setup forms
    setupCustomerForm();
    await setupContactForm();
    await setupDealForm();
    await setupTaskForm();
    
    // Load data for active section
    const activeSection = document.querySelector('.section.active');
    
    if (activeSection) {
        switch (activeSection.id) {
            case 'dashboard':
                await loadDashboard();
                break;
            case 'customers':
                await loadCustomers();
                break;
            case 'contacts':
                await loadContacts();
                break;
            case 'deals':
                await loadDeals();
                break;
            case 'tasks':
                await loadTasks();
                break;
        }
    }
    
    // Setup dashboard refresh button
    const refreshDashboardBtn = document.getElementById('refresh-dashboard');
    if (refreshDashboardBtn) {
        refreshDashboardBtn.addEventListener('click', loadDashboard);
    }
    
    // Add event listeners for navigation to load data when switching tabs
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', async () => {
            const section = item.getAttribute('data-section');
            
            switch (section) {
                case 'dashboard':
                    await loadDashboard();
                    break;
                case 'customers':
                    await loadCustomers();
                    break;
                case 'contacts':
                    await loadContacts();
                    break;
                case 'deals':
                    await loadDeals();
                    break;
                case 'tasks':
                    await loadTasks();
                    break;
            }
        });
    });
});
