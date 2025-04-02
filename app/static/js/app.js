document.addEventListener('DOMContentLoaded', function() {
    // Кнопка создания нового чата
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }
    
    // Обработчики для существующих чатов
    setupChatItemHandlers();
    
    // Обработка клавиш ввода (для отправки сообщения по Enter)
    setupMessageInputHandlers();
});

/**
 * Настройка обработчиков для элементов чата в боковой панели
 */
function setupChatItemHandlers() {
    // Обработчик кликов по элементам чата в боковой панели
    const chatItems = document.querySelectorAll('.chat-item');
    chatItems.forEach(item => {
        // Клик по элементу чата - переход к чату
        item.addEventListener('click', function(e) {
            if (!e.target.classList.contains('delete-chat-btn')) {
                const chatId = this.dataset.chatId;
                window.location.href = `/chat/${chatId}`;
            }
        });
    });
    
    // Обработчик кнопок удаления чата
    const deleteBtns = document.querySelectorAll('.delete-chat-btn');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const chatId = this.dataset.chatId;
            if (confirm('Вы действительно хотите удалить этот чат?')) {
                deleteChat(chatId);
            }
        });
    });
}

/**
 * Создание нового чата
 */
async function createNewChat() {
    try {
        const response = await fetch('/chat/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'title': 'Новый чат'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            window.location.href = `/chat/${data.id}`;
        } else {
            console.error('Ошибка создания чата');
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

/**
 * Удаление чата
 */
async function deleteChat(chatId) {
    try {
        const response = await fetch(`/chat/${chatId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Если мы находимся на странице этого чата, перенаправляем на главную
            if (window.location.pathname.includes(`/chat/${chatId}`)) {
                window.location.href = '/';
            } else {
                // Иначе просто удаляем элемент из DOM
                const chatElement = document.querySelector(`.chat-item[data-chat-id="${chatId}"]`);
                if (chatElement) {
                    chatElement.remove();
                }
            }
        } else {
            console.error('Ошибка удаления чата');
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

/**
 * Настройка обработчиков для поля ввода сообщения (отправка по Enter)
 */
function setupMessageInputHandlers() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            // Ctrl+Enter или просто Enter для отправки
            if ((e.ctrlKey && e.key === 'Enter') || (!e.shiftKey && e.key === 'Enter')) {
                e.preventDefault();
                const sendBtn = document.getElementById('sendMessageBtn');
                if (sendBtn) {
                    sendBtn.click();
                }
            }
        });
    }
} 