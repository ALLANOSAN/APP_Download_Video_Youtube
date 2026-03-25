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
try {
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(['lastSearch', 'lastResults'], (data) => {
      if (chrome.runtime.lastError) return;
      if (data.lastSearch) {
        searchInput.value = data.lastSearch;
      }
      if (data.lastResults && data.lastResults.length > 0) {
        displayResults(data.lastResults);
        showStatus(data.lastResults.length + ' vídeos (cache)');
      }
    });
  }
} catch (e) {
  console.log('Storage not available');
}

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
    
    if (!videos || videos.length === 0) {
      showStatus('Nenhum resultado encontrado', 'error');
      return;
    }

    // Salva no storage
    try {
      if (chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ lastSearch: query, lastResults: videos });
      }
    } catch (e) {}

    displayResults(videos);
    showStatus(videos.length + ' vídeos encontrados');
    
  } catch (error) {
    console.error('Search error:', error);
    showStatus('Erro: ' + error.message, 'error');
  }
}

async function searchYouTube(query) {
  const searchUrl = 'https://www.youtube.com/results?search_query=' + encodeURIComponent(query);
  
  const response = await fetch(searchUrl);
  
  if (!response.ok) {
    throw new Error('HTTP ' + response.status);
  }
  
  const html = await response.text();
  return extractVideosFromHtml(html);
}

function extractVideosFromHtml(html) {
  const videos = [];
  const seen = new Set();
  
  // Encontra todos os videoIds
  const videoIdRegex = /"videoId":"([a-zA-Z0-9_-]{11})"/g;
  let match;
  
  while ((match = videoIdRegex.exec(html)) !== null && videos.length < 50) {
    const videoId = match[1];
    if (seen.has(videoId)) continue;
    seen.add(videoId);
    
    // Busca contexto ao redor deste videoId
    const idPos = html.indexOf('"videoId":"' + videoId + '"');
    const contextStart = Math.max(0, idPos - 200);
    const contextEnd = Math.min(html.length, idPos + 3000);
    const context = html.substring(contextStart, contextEnd);
    
    // Extrai título
    let title = '';
    const titleMatch = context.match(/"title":\{"runs":\[\{"text":"([^"]+)"/);
    if (titleMatch) {
      title = decodeText(titleMatch[1]);
    }
    
    // Extrai canal
    let channel = '';
    const channelMatch = context.match(/"ownerText":\{"runs":\[\{"text":"([^"]+)"/);
    if (channelMatch) {
      channel = decodeText(channelMatch[1]);
    } else {
      const channelMatch2 = context.match(/"shortBylineText":\{"runs":\[\{"text":"([^"]+)"/);
      if (channelMatch2) {
        channel = decodeText(channelMatch2[1]);
      }
    }
    
    // Extrai duração
    let duration = '';
    const durationMatch = context.match(/"lengthText":\{[^}]*"simpleText":"([^"]+)"/);
    if (durationMatch) {
      duration = durationMatch[1];
    }
    
    // Extrai views
    let views = '';
    const viewsMatch = context.match(/"viewCountText":\{"simpleText":"([^"]+)"/);
    if (viewsMatch) {
      views = viewsMatch[1];
    } else {
      const viewsMatch2 = context.match(/"shortViewCountText":\{[^}]*"simpleText":"([^"]+)"/);
      if (viewsMatch2) {
        views = viewsMatch2[1];
      }
    }
    
    // Extrai data publicação
    let published = '';
    const pubMatch = context.match(/"publishedTimeText":\{"simpleText":"([^"]+)"/);
    if (pubMatch) {
      published = pubMatch[1];
    }
    
    // Só adiciona se tiver título válido
    if (title && title.length > 2) {
      videos.push({
        id: videoId,
        title: title,
        thumbnail: 'https://i.ytimg.com/vi/' + videoId + '/mqdefault.jpg',
        channel: channel,
        duration: duration || '',
        views: views,
        publishedTime: published,
        url: 'https://www.youtube.com/watch?v=' + videoId
      });
    }
  }
  
  return videos;
}

function decodeText(str) {
  if (!str) return '';
  return str
    .replace(/\\u([0-9a-fA-F]{4})/g, function(m, code) {
      return String.fromCharCode(parseInt(code, 16));
    })
    .replace(/\\n/g, ' ')
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, '\\');
}

function displayResults(videos) {
  resultsDiv.innerHTML = '';
  
  if (!videos || videos.length === 0) {
    resultsDiv.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><p>Nenhum resultado encontrado</p></div>';
    return;
  }
  
  for (let i = 0; i < videos.length; i++) {
    const video = videos[i];
    const card = document.createElement('div');
    card.className = 'video-card';
    
    let statsHtml = '';
    if (video.views) {
      statsHtml += '<span>👁 ' + video.views + '</span>';
    }
    if (video.publishedTime) {
      statsHtml += '<span>📅 ' + video.publishedTime + '</span>';
    }
    
    card.innerHTML = '<div class="video-thumbnail">' +
      '<img src="' + video.thumbnail + '" alt="" loading="lazy">' +
      (video.duration ? '<span class="video-duration">' + video.duration + '</span>' : '') +
      '</div>' +
      '<div class="video-info">' +
      '<div class="video-title" title="' + escapeHtml(video.title) + '">' + escapeHtml(video.title) + '</div>' +
      (video.channel ? '<div class="video-channel">' + escapeHtml(video.channel) + '</div>' : '') +
      '<div class="video-stats">' + statsHtml + '</div>' +
      '</div>';
    
    card.addEventListener('click', (function(url) {
      return function() {
        chrome.tabs.create({ url: url });
      };
    })(video.url));
    
    resultsDiv.appendChild(card);
  }
}

function showStatus(message, type) {
  statusDiv.innerHTML = message;
  statusDiv.className = 'status ' + (type || '');
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
