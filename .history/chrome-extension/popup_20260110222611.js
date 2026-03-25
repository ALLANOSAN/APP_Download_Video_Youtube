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
  if (hasMore) {
    showStatus(displayedCount + " de " + allVideos.length + " vídeos (role para mais)");
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
  return extractVideosFromHtml(html);
}

function extractVideosFromHtml(html) {
  const videos = [];
  const seen = new Set();

  // Encontra todos os videoIds (sem limite)
  const videoIdRegex = /"videoId":"([a-zA-Z0-9_-]{11})"/g;
  let match;

  while ((match = videoIdRegex.exec(html)) !== null) {
    const videoId = match[1];
    if (seen.has(videoId)) continue;
    seen.add(videoId);

    // Busca contexto ao redor deste videoId
    const idPos = html.indexOf('"videoId":"' + videoId + '"');
    const contextStart = Math.max(0, idPos - 200);
    const contextEnd = Math.min(html.length, idPos + 3000);
    const context = html.substring(contextStart, contextEnd);

    // Extrai título
    let title = "";
    const titleMatch = context.match(/"title":\{"runs":\[\{"text":"([^"]+)"/);
    if (titleMatch) {
      title = decodeText(titleMatch[1]);
    }

    // Extrai canal
    let channel = "";
    const channelMatch = context.match(
      /"ownerText":\{"runs":\[\{"text":"([^"]+)"/
    );
    if (channelMatch) {
      channel = decodeText(channelMatch[1]);
    } else {
      const channelMatch2 = context.match(
        /"shortBylineText":\{"runs":\[\{"text":"([^"]+)"/
      );
      if (channelMatch2) {
        channel = decodeText(channelMatch2[1]);
      }
    }

    // Extrai duração
    let duration = "";
    const durationMatch = context.match(
      /"lengthText":\{[^}]*"simpleText":"([^"]+)"/
    );
    if (durationMatch) {
      duration = durationMatch[1];
    }

    // Extrai views
    let views = "";
    const viewsMatch = context.match(
      /"viewCountText":\{"simpleText":"([^"]+)"/
    );
    if (viewsMatch) {
      views = viewsMatch[1];
    } else {
      const viewsMatch2 = context.match(
        /"shortViewCountText":\{[^}]*"simpleText":"([^"]+)"/
      );
      if (viewsMatch2) {
        views = viewsMatch2[1];
      }
    }

    // Extrai data publicação
    let published = "";
    const pubMatch = context.match(
      /"publishedTimeText":\{"simpleText":"([^"]+)"/
    );
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
