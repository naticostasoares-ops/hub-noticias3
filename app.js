let dbData = [];
let activeTab = 'hoje';

// Color maps for subjects
const SUBJECT_COLORS = {
    "Esporte": { bg: "bg-green-100", text: "text-green-800", border: "border-green-300" },
    "Economia": { bg: "bg-yellow-100", text: "text-yellow-800", border: "border-yellow-300" },
    "Justiça": { bg: "bg-purple-100", text: "text-purple-800", border: "border-purple-300" },
    "Saúde": { bg: "bg-pink-100", text: "text-pink-800", border: "border-pink-300" },
    "Ciência e Tecnologia": { bg: "bg-cyan-100", text: "text-cyan-800", border: "border-cyan-300" },
    "Meio Ambiente": { bg: "bg-emerald-100", text: "text-emerald-800", border: "border-emerald-300" },
    "Trabalho": { bg: "bg-orange-100", text: "text-orange-800", border: "border-orange-300" },
    "Cultura": { bg: "bg-indigo-100", text: "text-indigo-800", border: "border-indigo-300" },
    "Entretenimento e Mídia": { bg: "bg-red-100", text: "text-red-800", border: "border-red-300" },
    "Política": { bg: "bg-gray-100", text: "text-gray-800", border: "border-gray-300" },
    "Relações Internacionais": { bg: "bg-blue-100", text: "text-blue-800", border: "border-blue-300" },
    "Defesa e Segurança": { bg: "bg-rose-100", text: "text-rose-800", border: "border-rose-300" },
    "Indefinido": { bg: "bg-slate-100", text: "text-slate-800", border: "border-slate-300" }
};

document.addEventListener("DOMContentLoaded", () => {
    fetchData();
});

function fetchData() {
    fetch('database.json')
        .then(response => {
            if (!response.ok) throw new Error("Erro ao carregar base de dados");
            return response.json();
        })
        .then(data => {
            dbData = data;
            initializeDropdowns();
            renderHojeTab();
            applyFilters();
        })
        .catch(err => {
            console.error(err);
            // If local json doesn't exist yet, try to load empty or mock
            dbData = [];
            renderHojeTab();
        });
}

function initializeDropdowns() {
    const countries = new Set();
    const sources = new Set();

    dbData.forEach(item => {
        item.sources.forEach(src => {
            if (src.country) countries.add(src.country);
            if (src.name) sources.add(src.name);
        });
    });

    const countrySelect = document.getElementById("filter-country");
    const sourceSelect = document.getElementById("filter-source");

    countries.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        countrySelect.appendChild(opt);
    });

    sources.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = s;
        sourceSelect.appendChild(opt);
    });
}

function switchTab(tab) {
    activeTab = tab;
    
    const tabHoje = document.getElementById('tab-hoje');
    const tabBusca = document.getElementById('tab-busca');
    const secHoje = document.getElementById('section-hoje');
    const secBusca = document.getElementById('section-busca');

    if (tab === 'hoje') {
        tabHoje.className = "px-5 py-2.5 font-bold text-sm border-b-2 border-red-600 text-red-600 bg-red-50 sm:rounded-t";
        tabBusca.className = "px-5 py-2.5 font-bold text-sm border-b-2 border-transparent text-gray-600 hover:text-red-600 hover:bg-gray-50 sm:rounded-t";
        secHoje.classList.remove('hidden');
        secBusca.classList.add('hidden');
        renderHojeTab();
    } else {
        tabHoje.className = "px-5 py-2.5 font-bold text-sm border-b-2 border-transparent text-gray-600 hover:text-red-600 hover:bg-gray-50 sm:rounded-t";
        tabBusca.className = "px-5 py-2.5 font-bold text-sm border-b-2 border-red-600 text-red-600 bg-red-50 sm:rounded-t";
        secHoje.classList.add('hidden');
        secBusca.classList.remove('hidden');
    }
}

function getRelativeTime(isoString) {
    if (!isoString) return "Desconhecido";
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHrs < 1) {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        return `há ${diffMins} min`;
    }
    if (diffHrs < 24) {
        return `há ${diffHrs} h`;
    }
    const diffDays = Math.floor(diffHrs / 24);
    return `há ${diffDays} dia${diffDays > 1 ? 's' : ''}`;
}

function getBadgeColors(subject) {
    return SUBJECT_COLORS[subject] || SUBJECT_COLORS["Indefinido"];
}

function renderHojeTab() {
    const cardsContainer = document.getElementById('hoje-cards');
    const destaqueContainer = document.getElementById('hoje-destaque');
    const emptyContainer = document.getElementById('hoje-empty');
    const countSpan = document.getElementById('hoje-count');
    
    destaqueContainer.innerHTML = '';
    cardsContainer.innerHTML = '';

    const now = new Date();
    const cutoff = new Date(now.getTime() - (48 * 60 * 60 * 1000));

    // Filter articles from the last 48 hours
    const recentArticles = dbData.filter(item => {
        if (!item.published_at) return false;
        const pubDate = new Date(item.published_at);
        return pubDate >= cutoff && pubDate <= now;
    });

    if (recentArticles.length === 0) {
        destaqueContainer.classList.add('hidden');
        emptyContainer.classList.remove('hidden');
        countSpan.textContent = "0 notícias";
        return;
    }

    emptyContainer.classList.add('hidden');
    countSpan.textContent = `${recentArticles.length} notícia${recentArticles.length > 1 ? 's' : ''}`;

    // Sort newest first
    recentArticles.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));

    // Determine destaque: most relevant for Brazil + highest multi-source weight
    // Formula: relevance_brazil * 2.0 + len(sources) * 1.5
    let bestIndex = 0;
    let maxScore = -1;
    recentArticles.forEach((art, idx) => {
        const score = (art.relevance_brazil || 1) * 2.0 + (art.sources.length) * 1.5;
        if (score > maxScore) {
            maxScore = score;
            bestIndex = idx;
        }
    });

    const destaque = recentArticles[bestIndex];
    const cardsList = recentArticles.filter((_, idx) => idx !== bestIndex);

    // Render Destaque
    destaqueContainer.classList.remove('hidden');
    const colorsDest = getBadgeColors(destaque.subject_primary);
    
    let destSources = destaque.sources.map(s => `${s.name} (${s.country} - ${s.nature})`).join(', ');
    const deadLinkWarningDest = destaque.link_valid === false 
        ? `<div class="mt-2 text-xs font-bold text-red-600 uppercase">⚠ Link original fora do ar ou alterado!</div>` 
        : '';

    destaqueContainer.innerHTML = `
        <div class="bg-white border-2 border-red-600 rounded p-6 shadow-md flex flex-col justify-between">
            <div>
                <div class="flex flex-wrap items-center gap-2 mb-3">
                    <span class="px-2.5 py-0.5 rounded text-xs font-extrabold uppercase ${colorsDest.bg} ${colorsDest.text}">${destaque.subject_primary}</span>
                    ${destaque.subjects_secondary ? destaque.subjects_secondary.map(s => `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-200 text-gray-700">${s}</span>`).join('') : ''}
                    <span class="text-xs text-gray-500 font-bold uppercase tracking-wider ml-auto">${getRelativeTime(destaque.published_at)}</span>
                </div>
                <h3 class="text-2xl font-extrabold text-gray-900 tracking-tight la-prensa-header mb-2 leading-snug">
                    <a href="${destaque.sources[0].link}" target="_blank" class="hover:text-red-700 hover:underline">${destaque.title}</a>
                </h3>
                <p class="text-sm text-gray-700 leading-relaxed font-semibold italic mb-4">"${destaque.summary}"</p>
                ${deadLinkWarningDest}
            </div>
            <div class="border-t border-gray-200 pt-3 flex flex-wrap justify-between items-center text-xs text-gray-500">
                <div><strong>Tipo:</strong> ${destaque.type}</div>
                <div><strong>Fontes:</strong> ${destSources}</div>
            </div>
        </div>
    `;

    // Render Cards
    cardsList.forEach(art => {
        const colors = getBadgeColors(art.subject_primary);
        const artSources = art.sources.map(s => `${s.name} (${s.country})`).join(', ');
        const deadLinkWarning = art.link_valid === false 
            ? `<div class="mt-2 text-xs font-bold text-red-600 uppercase">⚠ Link original alterado ou offline!</div>` 
            : '';

        const card = document.createElement('div');
        card.className = "bg-white border border-gray-300 rounded p-4 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow";
        card.innerHTML = `
            <div>
                <div class="flex flex-wrap items-center gap-1.5 mb-2.5">
                    <span class="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${colors.bg} ${colors.text}">${art.subject_primary}</span>
                    <span class="text-[10px] text-gray-500 font-bold uppercase tracking-wider ml-auto">${getRelativeTime(art.published_at)}</span>
                </div>
                <h4 class="text-base font-extrabold text-gray-900 leading-snug mb-2 la-prensa-header">
                    <a href="${art.sources[0].link}" target="_blank" class="hover:text-red-700 hover:underline">${art.title}</a>
                </h4>
                <p class="text-xs text-gray-600 leading-relaxed mb-3">${art.summary}</p>
                ${deadLinkWarning}
            </div>
            <div class="border-t border-gray-100 pt-2.5 mt-2 flex flex-col text-[10px] text-gray-500 space-y-1">
                <div><strong>Tipo:</strong> ${art.type}</div>
                <div class="truncate"><strong>Fontes:</strong> ${artSources}</div>
            </div>
        `;
        cardsContainer.appendChild(card);
    });
}

function applyFilters() {
    const keyword = document.getElementById("filter-keyword").value.toLowerCase();
    const subject = document.getElementById("filter-subject").value;
    const type = document.getElementById("filter-type").value;
    const country = document.getElementById("filter-country").value;
    const source = document.getElementById("filter-source").value;
    const startDateVal = document.getElementById("filter-start-date").value;
    const endDateVal = document.getElementById("filter-end-date").value;

    const resultsContainer = document.getElementById("busca-results");
    resultsContainer.innerHTML = '';

    const filtered = dbData.filter(item => {
        // Keyword Search
        if (keyword) {
            const inTitle = item.title.toLowerCase().includes(keyword);
            const inSummary = item.summary.toLowerCase().includes(keyword);
            if (!inTitle && !inSummary) return false;
        }

        // Subject Match
        if (subject && item.subject_primary !== subject) return false;

        // Type Match
        if (type && item.type !== type) return false;

        // Date Range Match
        if (item.published_at) {
            const pubDate = new Date(item.published_at);
            if (startDateVal) {
                const sDate = new Date(startDateVal);
                if (pubDate < sDate) return false;
            }
            if (endDateVal) {
                const eDate = new Date(endDateVal);
                // End date inclusive to end of day
                eDate.setHours(23, 59, 59, 999);
                if (pubDate > eDate) return false;
            }
        }

        // Country Match (any of sources)
        if (country) {
            const hasCountry = item.sources.some(s => s.country === country);
            if (!hasCountry) return false;
        }

        // Source Match (any of sources)
        if (source) {
            const hasSource = item.sources.some(s => s.name === source);
            if (!hasSource) return false;
        }

        return true;
    });

    // Render results
    if (filtered.length === 0) {
        resultsContainer.innerHTML = `<div class="bg-white border border-gray-300 p-6 text-center text-gray-500 font-medium">Nenhum resultado corresponde aos filtros selecionados.</div>`;
        return;
    }

    // Sort newest first
    filtered.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));

    filtered.forEach(art => {
        const colors = getBadgeColors(art.subject_primary);
        const artSources = art.sources.map(s => `${s.name} (${s.country} - ${s.nature})`).join(', ');
        
        let dateStr = art.published_at ? new Date(art.published_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : "Sem data";

        const card = document.createElement('div');
        card.className = "bg-white border border-gray-300 rounded p-4 flex flex-col justify-between shadow-sm";
        card.innerHTML = `
            <div>
                <div class="flex flex-wrap items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${colors.bg} ${colors.text}">${art.subject_primary}</span>
                    ${art.subjects_secondary ? art.subjects_secondary.map(s => `<span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-gray-100 text-gray-600">${s}</span>`).join('') : ''}
                    <span class="text-[10px] text-gray-500 font-bold uppercase ml-auto">${dateStr}</span>
                </div>
                <h4 class="text-base font-extrabold text-gray-900 leading-snug mb-1.5 la-prensa-header">
                    <a href="${art.sources[0].link}" target="_blank" class="hover:text-red-700 hover:underline">${art.title}</a>
                </h4>
                <p class="text-xs text-gray-600 leading-relaxed mb-2">${art.summary}</p>
            </div>
            <div class="border-t border-gray-100 pt-2 flex flex-wrap justify-between items-center text-[10px] text-gray-500">
                <div><strong>Tipo:</strong> ${art.type}</div>
                <div><strong>Fontes:</strong> ${artSources}</div>
            </div>
        `;
        resultsContainer.appendChild(card);
    });
}

function toggleAudioWidget() {
    const widget = document.getElementById("audio-widget");
    const restoreBtn = document.getElementById("audio-widget-restore");
    const player = document.getElementById("audio-player");

    if (widget.classList.contains("hidden")) {
        widget.classList.remove("hidden");
        restoreBtn.classList.add("hidden");
    } else {
        widget.classList.add("hidden");
        restoreBtn.classList.remove("hidden");
        player.pause();
    }
}

function exportToPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    const keyword = document.getElementById("filter-keyword").value || "Nenhuma";
    const subject = document.getElementById("filter-subject").value || "Todos";
    const type = document.getElementById("filter-type").value || "Todos";
    const country = document.getElementById("filter-country").value || "Todos";
    const source = document.getElementById("filter-source").value || "Todos";
    const startDateVal = document.getElementById("filter-start-date").value || "Início";
    const endDateVal = document.getElementById("filter-end-date").value || "Hoje";

    // Gather filtered articles
    const filtered = dbData.filter(item => {
        if (keyword && keyword !== "Nenhuma") {
            const inTitle = item.title.toLowerCase().includes(keyword.toLowerCase());
            const inSummary = item.summary.toLowerCase().includes(keyword.toLowerCase());
            if (!inTitle && !inSummary) return false;
        }
        if (subject && subject !== "Todos" && item.subject_primary !== subject) return false;
        if (type && type !== "Todos" && item.type !== type) return false;
        if (item.published_at) {
            const pubDate = new Date(item.published_at);
            if (startDateVal && startDateVal !== "Início") {
                if (pubDate < new Date(startDateVal)) return false;
            }
            if (endDateVal && endDateVal !== "Hoje") {
                const eDate = new Date(endDateVal);
                eDate.setHours(23,59,59,999);
                if (pubDate > eDate) return false;
            }
        }
        if (country && country !== "Todos" && !item.sources.some(s => s.country === country)) return false;
        if (source && source !== "Todos" && !item.sources.some(s => s.name === source)) return false;
        return true;
    });

    // Header / Cover Info
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(196, 23, 12); // Red G1 accent
    doc.text("Relatório de Curadoria de Notícias", 14, 20);
    
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(100, 100, 100);
    doc.text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, 14, 27);
    
    // Draw box for filters
    doc.setFillColor(245, 245, 245);
    doc.rect(14, 32, 182, 35, "F");
    
    doc.setFont("helvetica", "bold");
    doc.setTextColor(50, 50, 50);
    doc.text("Filtros Aplicados:", 18, 38);
    
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.text(`Período: ${startDateVal} a ${endDateVal}`, 18, 44);
    doc.text(`Assunto: ${subject}`, 18, 49);
    doc.text(`Tipo de Texto: ${type}`, 18, 54);
    doc.text(`Palavra-chave: ${keyword}`, 18, 59);
    doc.text(`País/Veículo: ${country} / ${source}`, 18, 64);
    
    // Group filtered articles by subject_primary
    const grouped = {};
    filtered.forEach(art => {
        const cat = art.subject_primary || "Indefinido";
        if (!grouped[cat]) grouped[cat] = [];
        grouped[cat].push(art);
    });

    let y = 78;
    
    Object.keys(grouped).forEach(cat => {
        // Check page break for category title
        if (y > 260) {
            doc.addPage();
            y = 20;
        }
        
        doc.setFont("helvetica", "bold");
        doc.setFontSize(14);
        doc.setTextColor(196, 23, 12);
        doc.text(`Assunto: ${cat.toUpperCase()}`, 14, y);
        y += 8;
        
        grouped[cat].forEach(art => {
            // Check page break for article title + content
            if (y > 240) {
                doc.addPage();
                y = 20;
            }
            
            doc.setFont("helvetica", "bold");
            doc.setFontSize(11);
            doc.setTextColor(30, 30, 30);
            
            // Handle long titles wrapping
            const splitTitle = doc.splitTextToSize(art.title, 180);
            doc.text(splitTitle, 14, y);
            y += (splitTitle.length * 5);
            
            // Source & Date line
            doc.setFont("helvetica", "italic");
            doc.setFontSize(9);
            doc.setTextColor(120, 120, 120);
            const dateStr = art.published_at ? new Date(art.published_at).toLocaleDateString('pt-BR') : "Sem data";
            const sourcesStr = art.sources.map(s => `${s.name} (${s.country})`).join(', ');
            doc.text(`Fontes: ${sourcesStr} | Data: ${dateStr}`, 14, y);
            y += 5;
            
            // Summary text
            doc.setFont("helvetica", "normal");
            doc.setFontSize(9.5);
            doc.setTextColor(60, 60, 60);
            const splitSummary = doc.splitTextToSize(art.summary, 180);
            doc.text(splitSummary, 14, y);
            y += (splitSummary.length * 4.5) + 2;
            
            // Full written URL (extremely important for printed reports)
            doc.setFont("courier", "normal");
            doc.setFontSize(8);
            doc.setTextColor(80, 80, 80);
            const rawUrl = art.sources[0].link;
            const splitUrl = doc.splitTextToSize(`Endereço da notícia: ${rawUrl}`, 180);
            doc.text(splitUrl, 14, y);
            y += (splitUrl.length * 4) + 6; // Add space between articles
        });
        y += 4; // Add space between categories
    });
    
    // Save generated PDF
    doc.save("Relatorio_Curadoria_RI.pdf");
}
