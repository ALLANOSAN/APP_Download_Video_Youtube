// YouTube Search Pro - Background Service Worker

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'searchYouTube') {
    searchYouTube(request.query)
      .then(results => sendResponse({ success: true, data: results }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Indica que a resposta será assíncrona
  }
});

async function searchYouTube(query) {
  const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
  
  const response = await fetch(searchUrl, {
    headers: {
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }
  
  const html = await response.text();
  
  // Extrai o JSON inicial do YouTube (ytInitialData)
  let data = null;
  
  // Tenta vários padrões de extração
  const patterns = [
    /var ytInitialData = ({.*?});<\/script>/s,
    /ytInitialData\s*=\s*({.*?});/s,
    /window\["ytInitialData"\]\s*=\s*({.*?});/s
  ];
  
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match) {
      try {
        data = JSON.parse(match[1]);
        break;
      } catch (e) {
        continue;
      }
    }
  }
  
  if (!data) {
    // Tenta encontrar JSON em outro formato
    const jsonStart = html.indexOf('{"responseContext"');
    if (jsonStart !== -1) {
      let depth = 0;
      let jsonEnd = jsonStart;
      for (let i = jsonStart; i < html.length; i++) {
        if (html[i] === '{') depth++;
        else if (html[i] === '}') depth--;
        if (depth === 0) {
          jsonEnd = i + 1;
          break;
        }
      }
      try {
        data = JSON.parse(html.substring(jsonStart, jsonEnd));
      } catch (e) {
        throw new Error('Could not parse YouTube response');
      }
    } else {
      throw new Error('Could not find YouTube data');
    }
  }
  
  return parseYouTubeData(data);
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
