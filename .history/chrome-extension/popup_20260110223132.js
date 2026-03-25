// YouTube Search Pro - Popup Script

const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const resultsDiv = document.getElementById("results");
const statusDiv = document.getElementById("status");

// Estado do scroll infinito
let currentQuery = "";
let allVideos = [];
let displayedCount = 0;
let isLoading = false;
let hasMore = true;
let continuationToken = null;
let isLoadingMore = false;
const INITIAL_LOAD = 20;
const LOAD_MORE = 15;

// Event listeners
searchBtn.addEventListener("click", doSearch);
searchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    doSearch();
  }
});

// Scroll infinito
resultsDiv.addEventListener("scroll", () => {
  if (isLoading || isLoadingMore) return;
  
  const scrollTop = resultsDiv.scrollTop;
  const scrollHeight = resultsDiv.scrollHeight;
  const clientHeight = resultsDiv.clientHeight;
  
  // Carrega mais quando estiver a 80% do fim
  if (scrollTop + clientHeight >= scrollHeight * 0.8) {
    // Se ainda tem vídeos em buffer, mostra eles primeiro
    if (displayedCount < allVideos.length) {
      loadMoreResults();
    } 
    // Se acabou o buffer mas tem continuation token, busca mais do YouTube
    else if (continuationToken && !isLoadingMore) {
      loadNextPage();
    }
  }
});

// Restaura última busca do storage
try {
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["lastSearch", "lastResults"], (data) => {
      if (chrome.runtime.lastError) return;
      if (data.lastSearch) {
        searchInput.value = data.lastSearch;
        currentQuery = data.lastSearch;
      }
      if (data.lastResults && data.lastResults.length > 0) {
        allVideos = data.lastResults;
        displayedCount = 0;
        hasMore = true;
        loadMoreResults();
        showStatus(data.lastResults.length + " vídeos (cache)");
      }
    });
  }
} catch (e) {
  console.log("Storage not available");
}

async function doSearch() {
  const query = searchInput.value.trim();
  if (!query) {
    showStatus("Digite algo para buscar", "error");
    return;
  }

  // Reset estado
  currentQuery = query;
  allVideos = [];
  displayedCount = 0;
  hasMore = true;
  isLoading = true;
  continuationToken = null;
  isLoadingMore = false;
  resultsDiv.innerHTML = "";

  showStatus('<span class="loading-spinner"></span>Buscando...', "loading");

  try {
    const videos = await searchYouTube(query);

    if (!videos || videos.length === 0) {
      showStatus("Nenhum resultado encontrado", "error");
      isLoading = false;
      return;
    }

    allVideos = videos;
    
    // Salva no storage
    try {
      if (chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ lastSearch: query, lastResults: videos });
      }
    } catch (e) {}

    isLoading = false;
    loadMoreResults();
    
  } catch (error) {
    console.error("Search error:", error);
    showStatus("Erro: " + error.message, "error");
    isLoading = false;
  }
}

// Carrega próxima página do YouTube
async function loadNextPage() {
  if (!continuationToken || isLoadingMore) return;
  
  isLoadingMore = true;
  showStatus(allVideos.length + " vídeos - carregando mais...", "loading");
  
  try {
    const newVideos = await fetchContinuation(continuationToken);
    
    if (newVideos && newVideos.length > 0) {
      // Adiciona novos vídeos ao buffer
      const existingIds = new Set(allVideos.map(v => v.id));
      const uniqueNew = newVideos.filter(v => !existingIds.has(v.id));
      allVideos = allVideos.concat(uniqueNew);
      
      // Mostra os novos
      loadMoreResults();
    } else {
      continuationToken = null;
      hasMore = false;
    }
  } catch (error) {
    console.error("Continuation error:", error);
    continuationToken = null;
  }
  
  isLoadingMore = false;
  updateStatus();
}

function loadMoreResults() {
  if (isLoading || displayedCount >= allVideos.length) {
    hasMore = false;
    updateStatus();
    return;
  }
  
  isLoading = true;
  
  // Quantos carregar desta vez
  const toLoad = displayedCount === 0 ? INITIAL_LOAD : LOAD_MORE;
  const endIndex = Math.min(displayedCount + toLoad, allVideos.length);
  
  // Adiciona os vídeos
  for (let i = displayedCount; i < endIndex; i++) {
    appendVideoCard(allVideos[i]);
  }
  
  displayedCount = endIndex;
  hasMore = displayedCount < allVideos.length;
  isLoading = false;
  
  updateStatus();
}

function updateStatus() {
  if (isLoadingMore) {
    showStatus(displayedCount + " de " + allVideos.length + " vídeos - carregando mais...", "loading");
  } else if (displayedCount < allVideos.length || continuationToken) {
    showStatus(displayedCount + " de " + allVideos.length + "+ vídeos (role para mais)");
  } else {
    showStatus(allVideos.length + " vídeos encontrados");
  }
}

function appendVideoCard(video) {
  const card = document.createElement("div");
  card.className = "video-card";

  let statsHtml = "";
  if (video.views) {
    statsHtml += "<span>👁 " + video.views + "</span>";
  }
  if (video.publishedTime) {
    statsHtml += "<span>📅 " + video.publishedTime + "</span>";
  }

  card.innerHTML =
    '<div class="video-thumbnail">' +
    '<img src="' + video.thumbnail + '" alt="" loading="lazy">' +
    (video.duration ? '<span class="video-duration">' + video.duration + "</span>" : "") +
    "</div>" +
    '<div class="video-info">' +
    '<div class="video-title" title="' + escapeHtml(video.title) + '">' + escapeHtml(video.title) + "</div>" +
    (video.channel ? '<div class="video-channel">' + escapeHtml(video.channel) + "</div>" : "") +
    '<div class="video-stats">' + statsHtml + "</div>" +
    "</div>";

  card.addEventListener("click", function () {
    chrome.tabs.create({ url: video.url });
  });

  resultsDiv.appendChild(card);
}

async function searchYouTube(query) {
  const searchUrl =
    "https://www.youtube.com/results?search_query=" + encodeURIComponent(query);

  const response = await fetch(searchUrl);

  if (!response.ok) {
    throw new Error("HTTP " + response.status);
  }

  const html = await response.text();
  
  // Extrai continuation token para próximas páginas
  continuationToken = extractContinuationToken(html);
  
  return extractVideosFromHtml(html);
}

// Extrai o token de continuação do HTML
function extractContinuationToken(html) {
  // Padrão 1: continuationCommand
  let match = html.match(/"continuationCommand":\{"token":"([^"]+)"/);
  if (match) return match[1];
  
  // Padrão 2: continuation token direto
  match = html.match(/"token":"([^"]{50,})","targetId":"search-feed"/);
  if (match) return match[1];
  
  // Padrão 3: nextContinuationData
  match = html.match(/"nextContinuationData":\{"continuation":"([^"]+)"/);
  if (match) return match[1];
  
  return null;
}

// Busca próxima página usando continuation token
async function fetchContinuation(token) {
  const apiUrl = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false";
  
  const payload = {
    context: {
      client: {
        clientName: "WEB",
        clientVersion: "2.20240101.00.00",
        hl: "pt",
        gl: "BR"
      }
    },
    continuation: token
  };
  
  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      console.error("Continuation failed:", response.status);
      return [];
    }
    
    const data = await response.json();
    return extractVideosFromContinuation(data);
  } catch (error) {
    console.error("Fetch continuation error:", error);
    return [];
  }
}

// Extrai vídeos da resposta de continuation (JSON)
function extractVideosFromContinuation(data) {
  const videos = [];
  
  try {
    // Navega pela estrutura do JSON
    const actions = data.onResponseReceivedCommands || [];
    
    for (const action of actions) {
      const items = action.appendContinuationItemsAction?.continuationItems || [];
      
      for (const item of items) {
        // Vídeo normal
        const renderer = item.videoRenderer;
        if (renderer) {
          const video = parseVideoRenderer(renderer);
          if (video) videos.push(video);
        }
        
        // Próximo token de continuation
        const contItem = item.continuationItemRenderer;
        if (contItem) {
          const nextToken = contItem.continuationEndpoint?.continuationCommand?.token;
          if (nextToken) {
            continuationToken = nextToken;
          }
        }
      }
    }
  } catch (error) {
    console.error("Parse continuation error:", error);
  }
  
  return videos;
}

// Parseia um videoRenderer para objeto de vídeo
function parseVideoRenderer(renderer) {
  try {
    const videoId = renderer.videoId;
    if (!videoId) return null;
    
    // Título
    let title = "";
    if (renderer.title?.runs?.[0]?.text) {
      title = renderer.title.runs[0].text;
    } else if (renderer.title?.simpleText) {
      title = renderer.title.simpleText;
    }
    
    if (!title) return null;
    
    // Canal
    let channel = "";
    if (renderer.ownerText?.runs?.[0]?.text) {
      channel = renderer.ownerText.runs[0].text;
    } else if (renderer.shortBylineText?.runs?.[0]?.text) {
      channel = renderer.shortBylineText.runs[0].text;
    }
    
    // Duração
    let duration = "";
    if (renderer.lengthText?.simpleText) {
      duration = renderer.lengthText.simpleText;
    }
    
    // Views
    let views = "";
    if (renderer.viewCountText?.simpleText) {
      views = renderer.viewCountText.simpleText;
    } else if (renderer.shortViewCountText?.simpleText) {
      views = renderer.shortViewCountText.simpleText;
    }
    
    // Data publicação
    let published = "";
    if (renderer.publishedTimeText?.simpleText) {
      published = renderer.publishedTimeText.simpleText;
    }
    
    return {
      id: videoId,
      title: title,
      thumbnail: "https://i.ytimg.com/vi/" + videoId + "/mqdefault.jpg",
      channel: channel,
      duration: duration,
      views: views,
      publishedTime: published,
      url: "https://www.youtube.com/watch?v=" + videoId
    };
  } catch (error) {
    return null;
  }
}

function extractVideosFromHtml(html) {
  const videos = [];
  const seen = new Set();

  // Método 1: Extrair do ytInitialData (mais preciso)
  const ytDataMatch = html.match(/var ytInitialData = ({.*?});<\/script>/s);
  if (ytDataMatch) {
    try {
      const ytData = JSON.parse(ytDataMatch[1]);
      const contents = ytData?.contents?.twoColumnSearchResultsRenderer?.primaryContents?.sectionListRenderer?.contents || [];
      
      for (const section of contents) {
        const items = section?.itemSectionRenderer?.contents || [];
        for (const item of items) {
          if (item.videoRenderer) {
            const video = parseVideoRenderer(item.videoRenderer);
            if (video && !seen.has(video.id)) {
              seen.add(video.id);
              videos.push(video);
            }
          }
        }
      }
      
      if (videos.length > 0) {
        return videos;
      }
    } catch (e) {
      console.log("JSON parse failed, using regex fallback");
    }
  }

  // Método 2: Regex mais específico - busca videoRenderer completos
  const videoRendererRegex = /"videoRenderer":\{"videoId":"([a-zA-Z0-9_-]{11})"[^}]*?"title":\{"runs":\[\{"text":"([^"]+)"/g;
  let match;

  while ((match = videoRendererRegex.exec(html)) !== null) {
    const videoId = match[1];
    const title = decodeText(match[2]);
    
    if (seen.has(videoId)) continue;
    seen.add(videoId);

    // Busca contexto ao redor deste videoRenderer
    const idPos = html.indexOf('"videoRenderer":{"videoId":"' + videoId + '"');
    if (idPos === -1) continue;
    
    const contextStart = idPos;
    const contextEnd = Math.min(html.length, idPos + 2500);
    const context = html.substring(contextStart, contextEnd);

    // Extrai canal
    let channel = "";
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
    let duration = "";
    const durationMatch = context.match(/"lengthText":\{[^}]*"simpleText":"([^"]+)"/);
    if (durationMatch) {
      duration = durationMatch[1];
    }

    // Extrai views
    let views = "";
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
    let published = "";
    const pubMatch = context.match(/"publishedTimeText":\{"simpleText":"([^"]+)"/);
    if (pubMatch) {
      published = pubMatch[1];
    }

    // Só adiciona se tiver título válido
    if (title && title.length > 2) {
      videos.push({
        id: videoId,
        title: title,
        thumbnail: "https://i.ytimg.com/vi/" + videoId + "/mqdefault.jpg",
        channel: channel,
        duration: duration || "",
        views: views,
        publishedTime: published,
        url: "https://www.youtube.com/watch?v=" + videoId,
      });
    }
  }

  return videos;
}

function decodeText(str) {
  if (!str) return "";
  return str
    .replace(/\\u([0-9a-fA-F]{4})/g, function (m, code) {
      return String.fromCharCode(parseInt(code, 16));
    })
    .replace(/\\n/g, " ")
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, "\\");
}

function showStatus(message, type) {
  statusDiv.innerHTML = message;
  statusDiv.className = "status " + (type || "");
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
