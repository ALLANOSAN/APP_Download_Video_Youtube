// YouTube Search Pro - Background Service Worker

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'searchYouTube') {
    searchYouTube(request.query)
      .then(results => sendResponse({ success: true, data: results }))
      .catch(error => {
        console.error('Search error:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true; // Indica que a resposta será assíncrona
  }
});

async function searchYouTube(query) {
  // Usa a página de resultados do YouTube
  const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}&sp=EgIQAQ%253D%253D`;
  
  const response = await fetch(searchUrl);
  
  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }
  
  const html = await response.text();
  
  // Procura por ytInitialData no HTML
  const dataMatch = html.match(/ytInitialData\s*=\s*(\{.+?\});\s*<\/script>/);
  
  if (!dataMatch) {
    // Tenta método alternativo - busca por videoId diretamente
    return extractVideosFromHtml(html);
  }
  
  try {
    const data = JSON.parse(dataMatch[1]);
    return parseYouTubeData(data);
  } catch (e) {
    console.error('JSON parse error:', e);
    return extractVideosFromHtml(html);
  }
}

function extractVideosFromHtml(html) {
  // Método alternativo: extrai videoIds diretamente do HTML
  const videos = [];
  const videoPattern = /"videoId":"([a-zA-Z0-9_-]{11})"/g;
  const titlePattern = /"title":\{"runs":\[\{"text":"([^"]+)"\}\]/g;
  
  const videoIds = new Set();
  let match;
  
  while ((match = videoPattern.exec(html)) !== null) {
    const videoId = match[1];
    if (!videoIds.has(videoId) && videoIds.size < 15) {
      videoIds.add(videoId);
    }
  }
  
  // Extrai mais informações para cada vídeo
  for (const videoId of videoIds) {
    // Procura pelo contexto deste videoId
    const idIndex = html.indexOf(`"videoId":"${videoId}"`);
    if (idIndex === -1) continue;
    
    // Pega um trecho do HTML ao redor
    const start = Math.max(0, idIndex - 500);
    const end = Math.min(html.length, idIndex + 2000);
    const context = html.substring(start, end);
    
    // Extrai título
    const titleMatch = context.match(/"title":\{"runs":\[\{"text":"([^"]+)"\}\]/);
    const title = titleMatch ? titleMatch[1] : 'Vídeo do YouTube';
    
    // Extrai canal
    const channelMatch = context.match(/"ownerText":\{"runs":\[\{"text":"([^"]+)"\}/);
    const channel = channelMatch ? channelMatch[1] : '';
    
    // Extrai duração
    const durationMatch = context.match(/"lengthText":\{"accessibility"[^}]*\},"simpleText":"([^"]+)"\}/);
    const duration = durationMatch ? durationMatch[1] : '';
    
    // Extrai views
    const viewsMatch = context.match(/"viewCountText":\{"simpleText":"([^"]+)"\}/);
    const views = viewsMatch ? viewsMatch[1] : '';
    
    videos.push({
      id: videoId,
      title: decodeUnicode(title),
      thumbnail: `https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`,
      channel: decodeUnicode(channel),
      duration: duration,
      views: views,
      publishedTime: '',
      url: `https://www.youtube.com/watch?v=${videoId}`
    });
  }
  
  return videos;
}

function decodeUnicode(str) {
  return str.replace(/\\u([0-9a-fA-F]{4})/g, (match, code) => 
    String.fromCharCode(parseInt(code, 16))
  );
}

function parseYouTubeData(data) {
  const videos = [];
  
  try {
    const contents = data?.contents?.twoColumnSearchResultsRenderer?.primaryContents
      ?.sectionListRenderer?.contents;
    
    if (!contents) {
      console.log('No contents found in data');
      return videos;
    }
    
    for (const section of contents) {
      const items = section?.itemSectionRenderer?.contents;
      if (!items) continue;
      
      for (const item of items) {
        const videoData = item?.videoRenderer;
        if (!videoData || !videoData.videoId) continue;
        
        const video = {
          id: videoData.videoId,
          title: videoData.title?.runs?.[0]?.text || 'Sem título',
          thumbnail: `https://i.ytimg.com/vi/${videoData.videoId}/mqdefault.jpg`,
          channel: videoData.ownerText?.runs?.[0]?.text || '',
          duration: videoData.lengthText?.simpleText || 'Ao vivo',
          views: videoData.viewCountText?.simpleText || '',
          publishedTime: videoData.publishedTimeText?.simpleText || '',
          url: `https://www.youtube.com/watch?v=${videoData.videoId}`
        };
        
        videos.push(video);
        if (videos.length >= 15) break;
      }
      if (videos.length >= 15) break;
    }
  } catch (e) {
    console.error('Parse error:', e);
  }
  
  return videos;
}
