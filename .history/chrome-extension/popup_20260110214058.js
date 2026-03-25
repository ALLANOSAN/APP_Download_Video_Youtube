// YouTube Search Pro - Popup Script

const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const resultsDiv = document.getElementById('results');
const statusDiv = document.getElementById('status');

// Event listeners
searchBtn.addEventListener('click', doSearch);
searchInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    doSearch();
  }
});

// Restaura última busca do storage
chrome.storage.local.get(['lastSearch', 'lastResults'], (data) => {
  if (data.lastSearch) {
    searchInput.value = data.lastSearch;
  }
  if (data.lastResults) {
    displayResults(data.lastResults);
  }
});

async function doSearch() {
  const query = searchInput.value.trim();
  if (!query) {
    showStatus('Digite algo para buscar', 'error');
    return;
  }

  showStatus('<span class="loading-spinner"></span>Buscando...', 'loading');
  resultsDiv.innerHTML = '';

  try {
    const videos = await searchYouTube(query);
    
    if (videos.length === 0) {
      showStatus('Nenhum resultado encontrado', 'error');
      return;
    }

    // Salva no storage
    chrome.storage.local.set({
      lastSearch: query,
      lastResults: videos
    });

    displayResults(videos);
    showStatus(`${videos.length} vídeos encontrados`);
    
  } catch (error) {
    console.error('Search error:', error);
    showStatus('Erro na busca. Tente novamente.', 'error');
  }
}

async function searchYouTube(query) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      { action: 'searchYouTube', query: query },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        if (response && response.success) {
          resolve(response.data);
        } else {
          reject(new Error(response?.error || 'Erro desconhecido'));
        }
      }
    );
  });
}

function displayResults(videos) {
  resultsDiv.innerHTML = '';
  
  if (videos.length === 0) {
    resultsDiv.innerHTML = `
      <div class="empty-state">
        <div class="icon">🔍</div>
        <p>Nenhum resultado encontrado</p>
      </div>
    `;
    return;
  }
  
  for (const video of videos) {
    const card = document.createElement('div');
    card.className = 'video-card';
    card.dataset.url = video.url;
    
    // Formata views
    let viewsText = video.views;
    if (viewsText) {
      viewsText = viewsText.replace(' views', '').replace(' visualizações', '');
    }
    
    card.innerHTML = `
      <div class="video-thumbnail">
        <img src="${video.thumbnail}" alt="${escapeHtml(video.title)}" loading="lazy">
        <span class="video-duration">${video.duration}</span>
      </div>
      <div class="video-info">
        <div class="video-title" title="${escapeHtml(video.title)}">${escapeHtml(video.title)}</div>
        <div class="video-channel">${escapeHtml(video.channel)}</div>
        <div class="video-stats">
          ${viewsText ? `<span>👁 ${viewsText}</span>` : ''}
          ${video.publishedTime ? `<span>📅 ${video.publishedTime}</span>` : ''}
        </div>
      </div>
    `;
    
    card.addEventListener('click', () => {
      chrome.tabs.create({ url: video.url });
    });
    
    resultsDiv.appendChild(card);
  }
}

function showStatus(message, type = '') {
  statusDiv.innerHTML = message;
  statusDiv.className = 'status ' + type;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
