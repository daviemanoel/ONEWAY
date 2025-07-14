/**
 * JavaScript para funcionalidade de consulta do Mercado Pago no Django Admin
 * Projeto ONE WAY - Sistema de Gestão de Pedidos
 */

function consultarMP(paymentId) {
    if (!paymentId) {
        alert('Payment ID não disponível para consulta.');
        return;
    }
    
    // Botão que foi clicado
    const button = event.target;
    const originalText = button.innerHTML;
    
    // Visual de loading
    button.innerHTML = '⏳ Consultando...';
    button.disabled = true;
    
    // Fazer requisição para endpoint Django
    fetch('/consultar-mp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            payment_id: paymentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Atualizar status na tela
            const statusCell = button.closest('tr').querySelector('.field-status_display_admin span');
            if (statusCell && data.novo_status) {
                statusCell.textContent = data.status_display;
                statusCell.style.color = getStatusColor(data.novo_status);
            }
            
            // Feedback visual
            button.innerHTML = '✅ Atualizado';
            button.style.backgroundColor = '#28a745';
            
            // Mostrar detalhes se disponível
            if (data.detalhes) {
                console.log('Detalhes MP:', data.detalhes);
            }
            
            // Recarregar página após 2 segundos para refletir mudanças
            setTimeout(() => {
                window.location.reload();
            }, 2000);
            
        } else {
            // Erro na consulta
            button.innerHTML = '❌ Erro';
            button.style.backgroundColor = '#dc3545';
            alert('Erro ao consultar MP: ' + (data.error || 'Erro desconhecido'));
            
            // Restaurar botão após 3 segundos
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.backgroundColor = '';
                button.disabled = false;
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        button.innerHTML = '❌ Erro';
        button.style.backgroundColor = '#dc3545';
        alert('Erro de conexão ao consultar Mercado Pago');
        
        // Restaurar botão após 3 segundos
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.backgroundColor = '';
            button.disabled = false;
        }, 3000);
    });
}

function getStatusColor(status) {
    const colors = {
        'pending': '#ffc107',     // amarelo
        'approved': '#28a745',    // verde
        'in_process': '#17a2b8',  // azul
        'rejected': '#dc3545',    // vermelho
        'cancelled': '#6c757d',   // cinza
        'refunded': '#fd7e14',    // laranja
    };
    return colors[status] || '#6c757d';
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Inicialização quando DOM carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('Consultar MP JavaScript carregado.');
    
    // Adicionar estilo aos botões de consulta
    const buttons = document.querySelectorAll('button[onclick*="consultarMP"]');
    buttons.forEach(button => {
        button.style.cursor = 'pointer';
        button.style.padding = '4px 8px';
        button.style.borderRadius = '4px';
        button.style.border = '1px solid #007cba';
        button.style.backgroundColor = '#007cba';
        button.style.color = 'white';
        button.style.fontSize = '12px';
    });
});