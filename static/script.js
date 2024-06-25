
function openIframe(url) {
    var iframe = document.getElementById('site_iframe');
    iframe.src = url;
    
    var iframeContainer = document.getElementById('iframe_container');
    iframeContainer.style.display = 'block';

    var iframeBackground = document.getElementById('iframeBackground');
    iframeBackground.style.display = 'block';

    document.body.classList.add('no-scroll');
}

document.getElementById('iframeBackground').addEventListener('click', function() {
    var iframeContainer = document.getElementById('iframe_container');
    iframeContainer.style.display = 'none';
    
    var iframe = document.getElementById('site_iframe');
    iframe.src = '';

    // Também tornar o iframeBackground invisível
    var iframeBackground = document.getElementById('iframeBackground');
    iframeBackground.style.display = 'none';

    document.body.classList.remove('no-scroll');
});

function toggleFavorite(user_id, url) {
    var rateElement = document.getElementById('rate_' + url);
    var currentRate = parseInt(rateElement.innerText);
    var newRate = currentRate === 0 ? 1 : 0;

    // Atualiza a exibição do rate imediatamente
    rateElement.innerText = newRate;

    // Envia uma requisição POST para atualizar o rate no servidor
    fetch('/update_rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: user_id,
            url: url,
            rate: newRate
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao atualizar o rate');
        }
        return response.text();
    })
    .then(data => {
        console.log(data);
    })
    .catch(error => {
        console.error('Erro:', error);
        // Reverte a exibição do rate se ocorrer um erro
        rateElement.innerText = currentRate;
    });
}

