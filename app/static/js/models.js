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
 * Обновление списка моделей из Ollama
 */
async function refreshModels() {
    const refreshBtn = document.getElementById('refreshModelsBtn');
    refreshBtn.disabled = true;
    refreshBtn.textContent = 'Обновление...';
    
    try {
        const response = await fetch('/models/refresh');
        if (response.ok) {
            const models = await response.json();
            // Обновляем список моделей на странице
            updateModelsList(models);
        } else {
            showError('Ошибка обновления моделей');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка обновления моделей');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = 'Обновить список моделей';
    }
}

/**
 * Обновляет список моделей на странице
 */
function updateModelsList(models) {
    const modelsList = document.querySelector('.models-list');
    
    // Если нет моделей, показываем сообщение
    if (!models || models.length === 0) {
        modelsList.innerHTML = '<div class="empty-state">Нет доступных моделей. Установите модели через Ollama и нажмите "Обновить список моделей".</div>';
        return;
    }
    
    // Очищаем текущий список
    modelsList.innerHTML = '';
    
    // Добавляем модели
    models.forEach(model => {
        const modelHTML = `
            <div class="model-item" data-model-name="${model.name}">
                <div class="model-info">
                    <h3>${model.display_name}</h3>
                    <p>${model.description || `Модель ${model.name}`}</p>
                </div>
                <div class="model-actions">
                    <button class="edit-model-btn" data-model-name="${model.name}">Настроить</button>
                </div>
            </div>
        `;
        modelsList.insertAdjacentHTML('beforeend', modelHTML);
    });
    
    // Обновляем обработчики
    setupModelEditButtons();
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
 * Открытие модального окна настроек модели
 */
async function openModelSettings(modelName) {
    const modal = document.getElementById('modelSettingsModal');
    const currentModelName = document.getElementById('currentModelName');
    
    currentModelName.textContent = modelName;
    
    // Загрузить текущие настройки модели
    try {
        const response = await fetch(`/models/${modelName}/settings`);
        if (response.ok) {
            const settings = await response.json();
            
            // Заполнить форму
            document.getElementById('temperature').value = settings.temperature;
            document.getElementById('temperatureValue').textContent = settings.temperature;
            document.getElementById('maxTokens').value = settings.max_tokens;
            document.getElementById('systemPrompt').value = settings.system_prompt || '';
        }
    } catch (error) {
        console.error('Ошибка загрузки настроек:', error);
    }
    
    // Показать модальное окно
    modal.style.display = 'block';
}

/**
 * Сохранение настроек модели
 */
async function saveModelSettings() {
    const modal = document.getElementById('modelSettingsModal');
    const modelName = document.getElementById('currentModelName').textContent;
    const temperature = document.getElementById('temperature').value;
    const maxTokens = document.getElementById('maxTokens').value;
    const systemPrompt = document.getElementById('systemPrompt').value;
    
    try {
        const formData = new FormData();
        formData.append('temperature', temperature);
        formData.append('max_tokens', maxTokens);
        formData.append('system_prompt', systemPrompt);
        
        const response = await fetch(`/models/${modelName}/settings`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            // Закрыть модальное окно
            modal.style.display = 'none';
        } else {
            showError('Ошибка сохранения настроек');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка сохранения настроек');
    }
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
 * Показать сообщение об ошибке
 */
function showError(message) {
    console.error(message);
    alert(message);
}