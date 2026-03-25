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
  const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
  
  try {
    const response = await fetch(searchUrl);
    const html = await response.text();
    
    // Extrai o JSON inicial do YouTube (ytInitialData)
    const match = html.match(/var ytInitialData = ({.*?});<\/script>/s);
    if (!match) {
      // Tenta outro padrão
      const match2 = html.match(/ytInitialData\s*=\s*({.*?});/s);
      if (!match2) {
        throw new Error('Could not parse YouTube response');
      }
      return parseYouTubeData(JSON.parse(match2[1]));
    }
    
    const data = JSON.parse(match[1]);
    return parseYouTubeData(data);
    
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}

function parseYouTubeData(data) {
  const videos = [];
  
  try {
    // Navega pela estrutura do YouTube
    const contents = data?.contents?.twoColumnSearchResultsRenderer?.primaryContents
      ?.sectionListRenderer?.contents;
    
    if (!contents) return videos;
    
    for (const section of contents) {
      const items = section?.itemSectionRenderer?.contents;
      if (!items) continue;
      
      for (const item of items) {
        const videoData = item?.videoRenderer;
        if (!videoData) continue;
        
        const video = {
          id: videoData.videoId,
          title: videoData.title?.runs?.[0]?.text || 'Sem título',
          thumbnail: `https://i.ytimg.com/vi/${videoData.videoId}/mqdefault.jpg`,
          channel: videoData.ownerText?.runs?.[0]?.text || 'Canal desconhecido',
          duration: videoData.lengthText?.simpleText || 'Ao vivo',
          views: videoData.viewCountText?.simpleText || videoData.viewCountText?.runs?.[0]?.text || '',
          publishedTime: videoData.publishedTimeText?.simpleText || '',
          url: `https://www.youtube.com/watch?v=${videoData.videoId}`
        };
        
        videos.push(video);
        
        // Limita a 15 resultados
        if (videos.length >= 15) break;
      }
      
      if (videos.length >= 15) break;
    }
    
  } catch (e) {
    console.error('Parse error:', e);
  }
  
  return videos;
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
