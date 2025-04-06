document.addEventListener('DOMContentLoaded', function() {
    const refreshModelsBtn = document.getElementById('refreshModelsBtn');
    const addPromptBtn = document.getElementById('addPromptBtn');
    
    // Кнопка обновления списка моделей
    if (refreshModelsBtn) {
        refreshModelsBtn.addEventListener('click', refreshModels);
    }
    
    // Кнопка добавления шаблона промпта
    if (addPromptBtn) {
        addPromptBtn.addEventListener('click', openPromptModal);
    }
    
    // Настройка обработчиков для кнопок редактирования моделей
    setupModelEditButtons();
    
    // Загрузка списка шаблонов промптов
    loadPromptTemplates();
    
    // Настройка модального окна настроек модели
    setupModelSettingsModal();
    
    // Настройка модального окна добавления промпта
    setupPromptModal();
});

/**
 * Настройка обработчиков для кнопок редактирования моделей
 */
function setupModelEditButtons() {
    const editButtons = document.querySelectorAll('.edit-model-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modelName = this.dataset.modelName;
            openModelSettings(modelName);
        });
    });
}

/**
 * Загрузка списка моделей и отображение их на странице
 */
async function loadModelsList() {
    try {
        const response = await fetch('/models/list');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const models = await response.json();
        console.log('Загружено моделей:', models.length);
        
        // Получаем контейнер для карточек моделей
        const modelCardsContainer = document.getElementById('modelCards');
        if (!modelCardsContainer) {
            console.error('Контейнер для карточек моделей не найден');
            return;
        }
        
        // Очищаем контейнер
        modelCardsContainer.innerHTML = '';
        
        // Создаем карточки для каждой модели
        models.forEach(model => {
            // Создаем карточку модели
            const card = document.createElement('div');
            card.className = 'model-card';
            card.id = `model-card-${model.id}`;
            
            // Наполняем карточку контентом
            card.innerHTML = `
                <h3>${model.display_name || model.name}</h3>
                <p>${model.description || `Модель ${model.name}`}</p>
                <button class="settings-btn" data-model-id="${model.id}" data-model-name="${model.name}">Настройки</button>
            `;
            
            // Добавляем карточку в контейнер
            modelCardsContainer.appendChild(card);
            
            // Добавляем обработчик для кнопки настроек
            const settingsBtn = card.querySelector('.settings-btn');
            if (settingsBtn) {
                settingsBtn.addEventListener('click', function() {
                    const modelId = this.getAttribute('data-model-id');
                    const modelName = this.getAttribute('data-model-name');
                    openModelSettings(modelId, modelName);
                });
            }
        });
    } catch (error) {
        console.error('Ошибка загрузки моделей:', error);
        showToast('Ошибка загрузки списка моделей', 'error');
    }
}

/**
 * Обновление списка моделей с сервера
 */
async function refreshModels() {
    try {
        // Показываем индикатор загрузки
        showToast('Обновление списка моделей...', 'info');
        
        const response = await fetch('/models/refresh');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Обновлено моделей:', result.length);
        
        // Перезагружаем список моделей
        await loadModelsList();
        
        showToast('Список моделей успешно обновлен', 'success');
    } catch (error) {
        console.error('Ошибка обновления моделей:', error);
        showToast('Ошибка обновления моделей', 'error');
    }
}

/**
 * Открытие модального окна настроек модели
 */
function openModelSettings(modelId, modelName) {
    // Получаем модальное окно
    const modal = document.getElementById('modelSettingsModal');
    if (!modal) {
        console.error('Модальное окно настроек не найдено');
        return;
    }
    
    // Устанавливаем заголовок
    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.textContent = `Настройки модели ${modelName}`;
    }
    
    // Устанавливаем ID модели в скрытое поле
    const modelIdInput = document.getElementById('modelIdInput');
    if (modelIdInput) {
        modelIdInput.value = modelId;
    }
    
    // Загружаем текущие настройки модели
    loadModelSettingsForModal(modelId);
    
    // Отображаем модальное окно
    modal.style.display = 'block';
}

/**
 * Загрузка настроек модели для отображения в модальном окне
 */
async function loadModelSettingsForModal(modelId) {
    try {
        const response = await fetch(`/models/${modelId}/settings`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const settings = await response.json();
        console.log('Загружены настройки модели:', settings);
        
        // Заполняем форму настроек
        const temperatureInput = document.getElementById('temperatureInput');
        const topPInput = document.getElementById('topPInput');
        const topKInput = document.getElementById('topKInput');
        const systemPromptInput = document.getElementById('systemPromptTextarea');
        
        if (temperatureInput) temperatureInput.value = settings.temperature || '0.7';
        if (topPInput) topPInput.value = settings.top_p || '0.9';
        if (topKInput) topKInput.value = settings.top_k || '40';
        if (systemPromptInput) systemPromptInput.value = settings.system_prompt || '';
        
    } catch (error) {
        console.error('Ошибка загрузки настроек модели:', error);
        showToast('Ошибка загрузки настроек модели', 'error');
    }
}

/**
 * Сохранение настроек модели
 */
async function saveModelSettings(event) {
    event.preventDefault();
    
    const modelId = document.getElementById('modelIdInput').value;
    if (!modelId) {
        showToast('ID модели не указан', 'error');
        return;
    }
    
    const form = document.getElementById('modelSettingsForm');
    if (!form) {
        showToast('Форма настроек не найдена', 'error');
        return;
    }
    
    const formData = new FormData(form);
    
    try {
        const response = await fetch(`/models/${modelId}/settings`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Сохранены настройки модели:', result);
        
        // Закрываем модальное окно
        const modal = document.getElementById('modelSettingsModal');
        if (modal) {
            modal.style.display = 'none';
        }
        
        showToast('Настройки модели сохранены', 'success');
    } catch (error) {
        console.error('Ошибка сохранения настроек:', error);
        showToast('Ошибка сохранения настроек', 'error');
    }
}

/**
 * Вспомогательная функция для отображения уведомлений
 */
function showToast(message, type = 'info') {
    // Создаем элемент уведомления
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Добавляем в контейнер для уведомлений
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Если контейнера нет, создаем его
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
        container.appendChild(toast);
    } else {
        toastContainer.appendChild(toast);
    }
    
    // Автоматически удаляем через 3 секунды
    setTimeout(() => {
        toast.classList.add('toast-hidden');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

/**
 * Загрузка списка шаблонов промптов
 */
async function loadPromptTemplates() {
    try {
        const response = await fetch('/models/prompts/list');
        if (response.ok) {
            const templates = await response.json();
            updatePromptsList(templates);
        }
    } catch (error) {
        console.error('Ошибка загрузки шаблонов:', error);
    }
}

/**
 * Обновление списка шаблонов промптов
 */
function updatePromptsList(templates) {
    const promptsList = document.getElementById('promptsList');
    
    // Если нет шаблонов, показываем сообщение
    if (!templates || templates.length === 0) {
        promptsList.innerHTML = '<div class="empty-state">Нет созданных шаблонов промптов. Создайте новый шаблон с помощью кнопки "Добавить шаблон".</div>';
        return;
    }
    
    // Очищаем текущий список
    promptsList.innerHTML = '';
    
    // Добавляем шаблоны
    templates.forEach(template => {
        const promptHTML = `
            <div class="prompt-item" data-prompt-id="${template.id}">
                <div class="prompt-info">
                    <h3>${template.name}</h3>
                    ${template.description ? `<p>${template.description}</p>` : ''}
                </div>
                <div class="prompt-content">
                    <div class="prompt-section">
                        <h4>Системный промпт:</h4>
                        <pre>${template.system_prompt}</pre>
                    </div>
                    ${template.user_prompt ? `
                    <div class="prompt-section">
                        <h4>Шаблон сообщения пользователя:</h4>
                        <pre>${template.user_prompt}</pre>
                    </div>
                    ` : ''}
                </div>
                <div class="prompt-actions">
                    <button class="edit-prompt-btn" data-prompt-id="${template.id}">Редактировать</button>
                    <button class="delete-prompt-btn" data-prompt-id="${template.id}">Удалить</button>
                </div>
            </div>
        `;
        promptsList.insertAdjacentHTML('beforeend', promptHTML);
    });
    
    // Настраиваем обработчики для кнопок
    setupPromptButtons();
}

/**
 * Настройка обработчиков для кнопок редактирования и удаления промптов
 */
function setupPromptButtons() {
    // Кнопки редактирования
    const editButtons = document.querySelectorAll('.edit-prompt-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const promptId = this.dataset.promptId;
            editPromptTemplate(promptId);
        });
    });
    
    // Кнопки удаления
    const deleteButtons = document.querySelectorAll('.delete-prompt-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const promptId = this.dataset.promptId;
            if (confirm('Вы действительно хотите удалить этот шаблон?')) {
                deletePromptTemplate(promptId);
            }
        });
    });
}

/**
 * Настройка модального окна настроек модели
 */
function setupModelSettingsModal() {
    const modal = document.getElementById('modelSettingsModal');
    const closeBtn = modal.querySelector('.close-modal');
    const form = document.getElementById('modelSettingsForm');
    const temperatureSlider = document.getElementById('temperature');
    const temperatureValue = document.getElementById('temperatureValue');
    
    // Обработчик изменения значения температуры
    temperatureSlider.addEventListener('input', function() {
        temperatureValue.textContent = this.value;
    });
    
    // Закрытие модального окна
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Закрытие по клику вне модального окна
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Обработка отправки формы
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        saveModelSettings();
    });
}

/**
 * Настройка модального окна добавления/редактирования промпта
 */
function setupPromptModal() {
    const modal = document.getElementById('promptTemplateModal');
    const closeBtn = modal.querySelector('.close-modal');
    const form = document.getElementById('promptTemplateForm');
    
    // Закрытие модального окна
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Закрытие по клику вне модального окна
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Обработка отправки формы
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        savePromptTemplate();
    });
}

/**
 * Открытие модального окна для добавления нового шаблона
 */
function openPromptModal() {
    const modal = document.getElementById('promptTemplateModal');
    const modalTitle = document.getElementById('promptModalTitle');
    const form = document.getElementById('promptTemplateForm');
    
    // Сбросить форму
    form.reset();
    document.getElementById('promptId').value = '';
    
    // Установить заголовок
    modalTitle.textContent = 'Новый шаблон промпта';
    
    // Показать модальное окно
    modal.style.display = 'block';
}

/**
 * Редактирование существующего шаблона
 */
async function editPromptTemplate(promptId) {
    try {
        const response = await fetch('/models/prompts/list');
        if (response.ok) {
            const templates = await response.json();
            const template = templates.find(t => t.id == promptId);
            
            if (template) {
                const modal = document.getElementById('promptTemplateModal');
                const modalTitle = document.getElementById('promptModalTitle');
                
                // Заполнить форму
                document.getElementById('promptId').value = template.id;
                document.getElementById('promptName').value = template.name;
                document.getElementById('promptDescription').value = template.description || '';
                document.getElementById('promptSystemPrompt').value = template.system_prompt;
                document.getElementById('promptUserPrompt').value = template.user_prompt || '';
                
                // Установить заголовок
                modalTitle.textContent = 'Редактировать шаблон промпта';
                
                // Показать модальное окно
                modal.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки шаблона:', error);
    }
}

/**
 * Сохранение шаблона промпта
 */
async function savePromptTemplate() {
    const modal = document.getElementById('promptTemplateModal');
    const promptId = document.getElementById('promptId').value;
    const name = document.getElementById('promptName').value;
    const description = document.getElementById('promptDescription').value;
    const systemPrompt = document.getElementById('promptSystemPrompt').value;
    const userPrompt = document.getElementById('promptUserPrompt').value;
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('system_prompt', systemPrompt);
        
        if (description) {
            formData.append('description', description);
        }
        
        if (userPrompt) {
            formData.append('user_prompt', userPrompt);
        }
        
        // Используем POST для создания нового шаблона
        // (в будущем можно добавить PUT для обновления существующего)
        const response = await fetch('/models/prompts/create', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Закрыть модальное окно
            modal.style.display = 'none';
            
            // Обновить список шаблонов
            loadPromptTemplates();
        } else {
            showError('Ошибка сохранения шаблона');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка сохранения шаблона');
    }
}

/**
 * Удаление шаблона промпта
 */
async function deletePromptTemplate(promptId) {
    try {
        const response = await fetch(`/models/prompts/${promptId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Обновить список шаблонов
            loadPromptTemplates();
        } else {
            showError('Ошибка удаления шаблона');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка удаления шаблона');
    }
}

/**
 * Показывает сообщение об ошибке
 */
function showError(message) {
    // Удаляем старые сообщения об ошибках, если они есть
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    
    // Создаем элемент сообщения
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    
    // Добавляем элемент в DOM
    document.body.appendChild(errorElement);
    
    // Анимация появления
    setTimeout(() => {
        errorElement.classList.add('fade-in');
    }, 10);
    
    // Автоматическое скрытие через 5 секунд
    setTimeout(() => {
        errorElement.classList.add('fade-out');
        setTimeout(() => {
            errorElement.remove();
        }, 500);
    }, 5000);
}

/**
 * Показывает сообщение об успешном выполнении операции
 */
function showSuccess(message) {
    // Удаляем старые сообщения об успехе, если они есть
    document.querySelectorAll('.success-message').forEach(el => el.remove());
    
    // Создаем элемент сообщения
    const successElement = document.createElement('div');
    successElement.className = 'success-message';
    successElement.textContent = message;
    
    // Добавляем элемент в DOM
    document.body.appendChild(successElement);
    
    // Анимация появления
    setTimeout(() => {
        successElement.classList.add('fade-in');
    }, 10);
    
    // Автоматическое скрытие через 3 секунды
    setTimeout(() => {
        successElement.classList.add('fade-out');
        setTimeout(() => {
            successElement.remove();
        }, 500);
    }, 3000);
}