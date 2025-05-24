// Elementos do DOM
const monthSelect = document.getElementById('month-select');
const totalValue = document.getElementById('total-value');
const listaValue = document.getElementById('lista-value');
const pixValue = document.getElementById('pix-value');
const loadingIndicator = document.getElementById('loading');
const errorMessage = document.getElementById('error-message');
const dashboardContent = document.getElementById('dashboard-content');
const statusContent = document.getElementById('status-content');
const retryButton = document.getElementById('retry-button');
const useDemoDataButton = document.getElementById('use-demo-data');
const dataNotice = document.getElementById('data-notice');

// Novos elementos para os cards de estatísticas do PDV
const pdvTotalValue = document.getElementById('pdv-total-value');
const pdvListaValue = document.getElementById('pdv-lista-value');
const pdvPixValue = document.getElementById('pdv-pix-value');

// Novos botões para o gráfico unificado
const viewTopBtn = document.getElementById('view-top-btn');
const viewBottomBtn = document.getElementById('view-bottom-btn');
const pdvListaBtn = document.getElementById('pdv-lista-btn');
const pdvPixBtn = document.getElementById('pdv-pix-btn');

// Novos elementos para os gráficos temporais
const temporalMonthSelect = document.getElementById('temporal-month-select');
const temporalPdvSelect = document.getElementById('temporal-pdv-select');
const temporalMonthSerialSelect = document.getElementById('temporal-month-serial-select');
const temporalPdvSerialSelect = document.getElementById('temporal-pdv-serial-select');

// Cores para os tipos de pagamento
const COLOR_MAPPING = {
    'LISTA': '#0066cc',
    'PIX': '#4da6ff'
};

// Paleta de cores para múltiplos SERIAIS
const SERIAL_COLORS = [
    '#FF9800', '#E91E63', '#3F51B5', '#009688', '#8BC34A', '#FF5722', '#607D8B', '#9C27B0', '#00BCD4', '#CDDC39',
    '#F44336', '#2196F3', '#4CAF50', '#FFC107', '#795548', '#673AB7', '#00E676', '#FFB300', '#D84315', '#1E88E5',
    '#43A047', '#FDD835', '#6D4C41', '#C2185B', '#0288D1', '#388E3C', '#FFA726', '#5D4037', '#7B1FA2', '#00897B'
];

// Instâncias de gráficos
let lineChart, barChart, pdvChart;
let temporalPdvChart, temporalSerialChart;

// Tipo de pagamento atual para os gráficos de PDVs
let currentPaymentType = 'LISTA';
let currentPdvView = 'top'; // 'top' para maiores vendas, 'bottom' para menores vendas

// Flag para dados de demonstração
let useDemoData = false;

// Dados globais
let allData = {
    'Dezembro 2024': null,
    'Janeiro 2025': null,
    'Fevereiro 2025': null,
    'Março 2025': null,
    'Abril 2025': null,
    'Maio 2025': null
};

// Mapeamento de arquivos para meses
const fileToMonth = {
    'dezembro_24.csv': 'Dezembro 2024',
    'janeiro_25.csv': 'Janeiro 2025',
    'fevereiro_25.csv': 'Fevereiro 2025',
    'março_25.csv': 'Março 2025',
    'abril_25.csv': 'Abril 2025',
    'maio_25.csv': 'Maio 2025'
};

// Lista de formas de pagamento a serem excluídas (case insensitive)
const EXCLUDED_PAYMENT_TYPES = ['dinheiro'];

// Ordem cronológica dos meses
const monthOrder = [
    'Dezembro 2024',
    'Janeiro 2025',
    'Fevereiro 2025',
    'Março 2025',
    'Abril 2025',
    'Maio 2025'
];

// Formatar valores para moeda brasileira
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Mostrar indicador de carregamento
function showLoading() {
    loadingIndicator.style.display = 'block';
    dashboardContent.style.opacity = '0.5';
}

// Ocultar indicador de carregamento
function hideLoading() {
    loadingIndicator.style.display = 'none';
    dashboardContent.style.opacity = '1';
}

// Mostrar mensagem de erro
function showError() {
    errorMessage.style.display = 'block';
    dashboardContent.style.display = 'none';
}

// Ocultar mensagem de erro
function hideError() {
    errorMessage.style.display = 'none';
    dashboardContent.style.display = 'grid';
}

// Mostrar aviso de dados simulados
function showDataNotice(message) {
    dataNotice.innerHTML = message;
    dataNotice.style.display = 'block';
}

// Ocultar aviso de dados simulados
function hideDataNotice() {
    dataNotice.style.display = 'none';
}

// Atualizar status de carregamento
function updateStatus(month, success, message = '') {
    const statusItem = document.createElement('div');
    statusItem.className = 'status-item';
    statusItem.innerHTML = `
        <span>${month}</span>
        <span class="status-${success ? 'success' : 'error'}">${success ? 'Carregado' : 'Erro'}${message ? ': ' + message : ''}</span>
    `;
    statusContent.appendChild(statusItem);
    console.log(`Status: ${month} - ${success ? 'Sucesso' : 'Erro'} ${message}`);
}

// Carregar dados simulados para quando os arquivos CSV não estiverem disponíveis
function getSimulatedData(month) {
    // Garantir que não tenha a forma de pagamento "DINHEIRO" nos dados simulados
    const baseValues = {
        'Dezembro 2024': { 'LISTA': 62457890.50, 'PIX': 28765430.25 },
        'Janeiro 2025': { 'LISTA': 35782450.25, 'PIX': 15438765.75 },
        'Fevereiro 2025': { 'LISTA': 38945620.50, 'PIX': 17654320.25 },
        'Março 2025': { 'LISTA': 42567890.75, 'PIX': 20784365.50 },
        'Abril 2025': { 'LISTA': 45892750.25, 'PIX': 24568920.50 },
        'Maio 2025': { 'LISTA': 49217610.75, 'PIX': 28353475.75 }
    };

    const data = baseValues[month] || { 'LISTA': 10000000, 'PIX': 5000000 };
    
    // Remover explicitamente qualquer forma de pagamento excluída
    EXCLUDED_PAYMENT_TYPES.forEach(type => {
        if (data[type]) {
            delete data[type];
        }
    });
    
    // Dados simulados de PDVs
    const pdvData = {
        'LISTA': {
            'Metrô Itaquera AA': 8945620.75,
            'Metrô Tatuapé AA': 7654380.50,
            'Metrô Sé CC': 6543290.25,
            'Terminal Jabaquara BB': 5432180.50,
            'Terminal Pinheiros AA': 4321070.75,
            'Terminal Sacomã CC': 3210960.50,
            'Terminal Santo Amaro AA': 2109850.25,
            'Terminal Vila Prudente BB': 1098740.50,
            'Metrô República DD': 987630.25,
            'Terminal Campo Limpo AA': 876520.50
        },
        'PIX': {
            'Terminal Jabaquara BB': 5432180.50,
            'Metrô Tatuapé AA': 4321070.75,
            'Metrô Itaquera AA': 3210960.50,
            'Terminal Santo Amaro AA': 2109850.25,
            'Metrô Sé CC': 1098740.50,
            'Terminal Pinheiros AA': 987630.25,
            'Terminal Vila Prudente BB': 876520.50,
            'Terminal Sacomã CC': 765410.25,
            'Terminal Campo Limpo AA': 654300.50,
            'Metrô República DD': 543210.25
        }
    };
    
    const total = Object.values(data).reduce((sum, value) => sum + value, 0);
    return {
        groupedData: data,
        total: total,
        paymentTypes: Object.keys(data),
        pdvData: pdvData,
        isSimulated: true
    };
}

// Carregar dados de demonstração para todos os meses
function loadDemoData() {
    statusContent.innerHTML = '';
    
    for (const month of monthOrder) {
        allData[month] = getSimulatedData(month);
        updateStatus(month, true, '(dados simulados)');
    }
    
    useDemoData = true;
    showDataNotice('Atenção: Exibindo dados simulados para demonstração. Os valores não representam dados reais.');
    
    updateDashboard();
    hideError();
    return true;
}

// Carregar todos os arquivos CSV
async function loadAllData() {
    statusContent.innerHTML = '';
    hideDataNotice();
    useDemoData = false;
    let hasAnySuccessfulLoad = false;
    let hasAnySimulatedData = false;
    let erroredFiles = [];

    for (const file of Object.keys(fileToMonth)) {
        const month = fileToMonth[file];
        try {
            console.log(`Tentando carregar: ${file}`);
            const response = await fetch(file);
            if (!response.ok) {
                throw new Error(`Falha ao carregar arquivo: ${response.status}`);
            }
            const csvText = await response.text();
            if (!csvText || csvText.trim() === '') {
                throw new Error('Arquivo vazio');
            }
            Papa.parse(csvText, {
                header: true,
                skipEmptyLines: true,
                dynamicTyping: true,
                delimiter: ';',
                complete: (results) => {
                    if (results.data && results.data.length > 0) {
                        const processedData = processData(results.data, results.meta.fields);
                        if (processedData) {
                            allData[month] = processedData;
                            updateStatus(month, true);
                            hasAnySuccessfulLoad = true;
                        } else {
                            erroredFiles.push(file);
                            throw new Error('Falha ao processar dados');
                        }
                    } else {
                        erroredFiles.push(file);
                        throw new Error('Sem dados suficientes');
                    }
                },
                error: (error) => {
                    erroredFiles.push(file);
                    throw error;
                }
            });
        } catch (error) {
            console.error(`Erro ao carregar ${file}:`, error);
            erroredFiles.push(file);
            // Usar dados simulados em caso de erro
            allData[month] = getSimulatedData(month);
            updateStatus(month, false, error.message + ' (usando dados simulados)');
            hasAnySimulatedData = true;
            hasAnySuccessfulLoad = true;
        }
    }

    if (erroredFiles.length > 0) {
        showError();
        errorMessage.innerHTML = `<p>Erro ao carregar os arquivos CSV: <b>${erroredFiles.join(', ')}</b>.<br>Verifique se os arquivos estão na pasta correta, com o nome correto e com conteúdo válido.</p>`;
    } else if (hasAnySimulatedData) {
        showDataNotice('Atenção: Alguns meses estão exibindo dados simulados porque não foi possível carregar os arquivos CSV originais.');
    }

    return hasAnySuccessfulLoad;
}

// Processar dados do CSV
function processData(data, fields) {
    // Mapear nomes de colunas baseado nos cabeçalhos do CSV
    const columnMapping = {};
    // Buscar colunas relevantes a partir dos cabeçalhos
    for (const field of fields) {
        const upperField = field.toUpperCase();
        if (upperField.includes('TIPO') && upperField.includes('PAGAMENTO')) {
            columnMapping.paymentType = field;
        } else if ((upperField.includes('VALOR') && upperField.includes('PAGO')) || upperField === 'VALOR' || upperField === 'VALOR DA RECARGA') {
            columnMapping.value = field;
        } else if (upperField === 'PDV' || upperField.includes('PDV')) {
            columnMapping.pdv = field;
        } else if (upperField.includes('SERIAL')) {
            columnMapping.serial = field;
        } else if (upperField.startsWith('DATA')) {
            columnMapping.data = field;
        }
    }
    // Fallback para data caso não encontre por DATA
    if (!columnMapping.data) {
        for (const field of fields) {
            if (field.toUpperCase().includes('DATA')) {
                columnMapping.data = field;
                break;
            }
        }
    }
    // Verificar se encontramos as colunas necessárias para os gráficos principais
    if (!columnMapping.paymentType || !columnMapping.value) {
        console.error('Colunas necessárias não encontradas:', columnMapping);
        return null;
    }
    // Agrupar por tipo de pagamento
    const groupedData = {};
    let total = 0;
    // Agrupar por PDV por tipo de pagamento
    const pdvData = {
        'LISTA': {},
        'PIX': {}
    };
    // Conjunto para armazenar todos os PDVs únicos
    const uniquePdvs = new Set();
    data.forEach((row, index) => {
        const paymentType = row[columnMapping.paymentType];
        const pdv = columnMapping.pdv ? row[columnMapping.pdv] : undefined;
        let value = row[columnMapping.value];
        // Converter para número se for string
        if (typeof value === 'string') value = parseFloat(value.replace(',', '.'));
        // Verificar se paymentType é válido
        if (paymentType && !isNaN(value)) {
            const normalizedType = paymentType.toUpperCase();
            if (!EXCLUDED_PAYMENT_TYPES.some(excluded => normalizedType === excluded.toUpperCase())) {
                // Agrupar por tipo de pagamento
                if (!groupedData[paymentType]) groupedData[paymentType] = 0;
                groupedData[paymentType] += value;
                total += value;
                // Agrupar por PDV para cada tipo de pagamento
                if (pdv && (normalizedType === 'LISTA' || normalizedType === 'PIX')) {
                    uniquePdvs.add(pdv);
                    if (!pdvData[normalizedType]) pdvData[normalizedType] = {};
                    if (!pdvData[normalizedType][pdv]) pdvData[normalizedType][pdv] = 0;
                    pdvData[normalizedType][pdv] += value;
                }
            }
        }
    });
    // Se não conseguimos extrair nenhum dado, retorna null
    if (Object.keys(groupedData).length === 0) {
        console.error('Nenhum dado válido encontrado');
        return null;
    }
    return {
        groupedData,
        total,
        paymentTypes: Object.keys(groupedData),
        pdvData,
        isSimulated: false,
        rawRows: data,
        columnMapping: {
            paymentType: columnMapping.paymentType,
            value: columnMapping.value,
            pdv: columnMapping.pdv,
            serial: columnMapping.serial,
            data: columnMapping.data
        }
    };
}

// Inicializar gráfico de linha
function initLineChart() {
    const ctx = document.getElementById('line-chart').getContext('2d');
    
    if (lineChart) {
        lineChart.destroy();
    }
    
    // Mostrar apenas dados do tipo LISTA para o gráfico de barras
    const datasets = [];
    const type = 'LISTA';
    
    // Verificar e registrar no console todos os valores disponíveis para depuração
    console.log("Verificando dados para LISTA em cada mês:");
    monthOrder.forEach(month => {
        if (allData[month]) {
            console.log(`${month}:`, allData[month].groupedData);
        }
    });
    
    const data = monthOrder.map(month => {
        if (allData[month] && allData[month].groupedData) {
            // Procurar por LISTA em qualquer capitalização
            for (const key in allData[month].groupedData) {
                if (key.toUpperCase() === 'LISTA') {
                    console.log(`Encontrado LISTA em ${month}:`, key, allData[month].groupedData[key]);
                    return allData[month].groupedData[key];
                }
            }
        }
        console.log(`Nenhum valor LISTA encontrado para ${month}`);
        return null;
    });
    
    console.log("Valores finais para o gráfico LISTA:", data);
    
    datasets.push({
        label: type,
        data: data,
        backgroundColor: COLOR_MAPPING[type] || getRandomColor(type),
        borderColor: (COLOR_MAPPING[type] || getRandomColor(type)),
        borderWidth: 1
    });
    
    lineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: monthOrder,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Evolução de Vendas - LISTA'
                }
            }
        }
    });
}

// Inicializar gráfico de barras
function initBarChart() {
    const ctx = document.getElementById('bar-chart').getContext('2d');
    
    if (barChart) {
        barChart.destroy();
    }
    
    // Mostrar apenas dados do tipo PIX para o gráfico de barras
    const labels = monthOrder;
    const datasets = [];
    const type = 'PIX';
    
    // Verificar e registrar no console todos os valores disponíveis para depuração
    console.log("Verificando dados para PIX em cada mês:");
    monthOrder.forEach(month => {
        if (allData[month]) {
            console.log(`${month}:`, allData[month].groupedData);
        }
    });
    
    const data = monthOrder.map(month => {
        if (allData[month] && allData[month].groupedData) {
            // Procurar por PIX em qualquer capitalização
            for (const key in allData[month].groupedData) {
                if (key.toUpperCase() === 'PIX') {
                    console.log(`Encontrado PIX em ${month}:`, key, allData[month].groupedData[key]);
                    return allData[month].groupedData[key];
                }
            }
        }
        console.log(`Nenhum valor PIX encontrado para ${month}`);
        return 0;
    });
    
    console.log("Valores finais para o gráfico PIX:", data);
    
    datasets.push({
        label: type,
        data: data,
        backgroundColor: COLOR_MAPPING[type] || getRandomColor(type)
    });
    
    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Vendas PIX por Mês'
                }
            }
        }
    });
}

// Gerar cor aleatória para tipos não mapeados
function getRandomColor(seed) {
    // Gera uma cor baseada no texto para ser consistente
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
        hash = seed.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    let color = '#';
    for (let i = 0; i < 3; i++) {
        const value = (hash >> (i * 8)) & 0xFF;
        color += ('00' + value.toString(16)).substr(-2);
    }
    
    return color;
}

// Inicializar gráfico de PDVs
function initPdvChart() {
    const ctx = document.getElementById('pdv-chart').getContext('2d');
    
    if (pdvChart) {
        pdvChart.destroy();
    }
    
    const selectedFile = monthSelect.value;
    const selectedMonth = fileToMonth[selectedFile];
    const data = allData[selectedMonth];
    
    console.log(`Dados para ${currentPdvView === 'top' ? 'TOP' : 'BOTTOM'} PDVs:`, data);
    console.log("Tipo de pagamento atual para PDVs:", currentPaymentType);
    
    // Se não tiver dados de PDV, gere dados simulados para demonstração
    if (!data || !data.pdvData || !data.pdvData[currentPaymentType] || 
        Object.keys(data.pdvData[currentPaymentType]).length === 0) {
        console.warn(`Dados reais de PDV não encontrados para ${currentPaymentType}, usando dados simulados`);
        
        // Dados simulados para demonstração
        const simulatedPdvData = {
            'LISTA': {
                'PDV Itaquera A': 8945620.75,
                'PDV Tatuapé B': 7654380.50,
                'PDV Sé C': 6543290.25,
                'PDV Jabaquara D': 5432180.50,
                'PDV Pinheiros E': 4321070.75,
                'PDV Sacomã F': 3210960.50,
                'PDV Santo Amaro G': 2109850.25,
                'PDV Vila Prudente H': 1098740.50,
                'PDV República I': 987630.25,
                'PDV Campo Limpo J': 876520.50,
                'PDV Remoto A': 120.50,
                'PDV Remoto B': 238.75,
                'PDV Remoto C': 342.25,
                'PDV Remoto D': 456.50,
                'PDV Remoto E': 560.75,
                'PDV Remoto F': 678.50,
                'PDV Remoto G': 782.25,
                'PDV Remoto H': 896.50,
                'PDV Remoto I': 953.25,
                'PDV Remoto J': 1087.75
            },
            'PIX': {
                'PDV Jabaquara D': 5432180.50,
                'PDV Tatuapé B': 4321070.75,
                'PDV Itaquera A': 3210960.50,
                'PDV Santo Amaro G': 2109850.25,
                'PDV Sé C': 1098740.50,
                'PDV Pinheiros E': 987630.25,
                'PDV Vila Prudente H': 876520.50,
                'PDV Sacomã F': 765410.25,
                'PDV Campo Limpo J': 654300.50,
                'PDV República I': 543210.25,
                'PDV Remoto K': 110.25,
                'PDV Remoto L': 225.50,
                'PDV Remoto M': 335.75,
                'PDV Remoto N': 445.25,
                'PDV Remoto O': 556.50,
                'PDV Remoto P': 667.75,
                'PDV Remoto Q': 778.25,
                'PDV Remoto R': 889.50,
                'PDV Remoto S': 945.75,
                'PDV Remoto T': 1056.25
            }
        };
        
        // Usar os dados simulados
        const pdvValues = simulatedPdvData[currentPaymentType];
        let sortedPdvs = Object.entries(pdvValues);
        
        if (currentPdvView === 'top') {
            // Ordenar do maior para o menor para TOP PDVs
            sortedPdvs = sortedPdvs.sort((a, b) => b[1] - a[1]);
        } else {
            // Ordenar do menor para o maior para BOTTOM PDVs
            sortedPdvs = sortedPdvs
                .filter(entry => entry[1] > 0) // Filtrar valores maiores que zero
                .sort((a, b) => a[1] - b[1]); // Ordenar do menor para o maior
        }
        
        // Pegar apenas os primeiros 10
        sortedPdvs = sortedPdvs.slice(0, 10);
        
        const pdvNames = sortedPdvs.map(item => item[0]);
        const pdvAmounts = sortedPdvs.map(item => item[1]);
        
        showDataNotice(`Atenção: Exibindo dados simulados para o ${currentPdvView === 'top' ? 'TOP' : 'BOTTOM'} 10 PDVs.`);
        
        renderPdvChart(pdvNames, pdvAmounts);
        return;
    }
    
    // Obter os PDVs com pelo menos uma venda
    const pdvValues = data.pdvData[currentPaymentType];
    
    // Filtrar PDVs com valor maior que zero
    let filteredPdvs = Object.entries(pdvValues)
        .filter(entry => entry[1] > 0);
    
    if (currentPdvView === 'top') {
        // Ordenar do maior para o menor para TOP PDVs
        filteredPdvs = filteredPdvs.sort((a, b) => b[1] - a[1]);
    } else {
        // Ordenar do menor para o maior para BOTTOM PDVs
        filteredPdvs = filteredPdvs.sort((a, b) => a[1] - b[1]);
    }
    
    // Pegar apenas os primeiros 10
    filteredPdvs = filteredPdvs.slice(0, 10);
    
    const pdvNames = filteredPdvs.map(item => item[0]);
    const pdvAmounts = filteredPdvs.map(item => item[1]);
    
    hideDataNotice(); // Ocultar aviso de dados simulados, pois estamos usando dados reais
    renderPdvChart(pdvNames, pdvAmounts);
}

// Renderizar o gráfico de PDVs
function renderPdvChart(pdvNames, pdvAmounts) {
    const ctx = document.getElementById('pdv-chart').getContext('2d');
    const color = COLOR_MAPPING[currentPaymentType] || getRandomColor(currentPaymentType);
    
    pdvChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: pdvNames,
            datasets: [{
                label: `Valor (${currentPaymentType})`,
                data: pdvAmounts,
                backgroundColor: color,
                borderColor: color,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: `${currentPdvView === 'top' ? 'TOP' : 'BOTTOM'} 10 PDVs - ${currentPaymentType}`
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                }
            }
        }
    });
}

// Preencher filtros de mês e PDV para os gráficos temporais
function fillTemporalFilters() {
    // Preencher meses
    if (temporalMonthSelect) {
        temporalMonthSelect.innerHTML = '';
        for (const file in fileToMonth) {
            const month = fileToMonth[file];
            const opt1 = document.createElement('option');
            opt1.value = month;
            opt1.textContent = month;
            temporalMonthSelect.appendChild(opt1);
        }
    }
    // Preencher PDVs iniciais
    updateTemporalPdvOptions();
}

function updateTemporalPdvOptions() {
    if (!temporalMonthSelect || !temporalPdvSelect) return;
    const month = temporalMonthSelect.value;
    temporalPdvSelect.innerHTML = '';
    if (allData[month] && allData[month].pdvData) {
        const pdvs = new Set([
            ...Object.keys(allData[month].pdvData['LISTA'] || {}),
            ...Object.keys(allData[month].pdvData['PIX'] || {})
        ]);
        Array.from(pdvs).sort().forEach(pdv => {
            const opt = document.createElement('option');
            opt.value = pdv;
            opt.textContent = pdv;
            temporalPdvSelect.appendChild(opt);
        });
    }
}

// Função utilitária para ajustar o tamanho do canvas ao container
function resizeCanvasToContainer(canvas) {
    const container = canvas.parentElement;
    if (container) {
        const dpr = window.devicePixelRatio || 1;
        const width = container.offsetWidth;
        const height = container.offsetHeight;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
    }
}

// Gráfico de série temporal por PDV
function renderTemporalPdvChart() {
    const month = temporalMonthSelect.value;
    const pdv = temporalPdvSelect.value;
    if (!month || !pdv || !allData[month]) return;
    const data = allData[month];
    // Agrupar vendas por data para o PDV selecionado (LISTA + PIX)
    const dailyTotals = {};
    data.rawRows.forEach(row => {
        if (row[data.columnMapping.pdv] === pdv) {
            const date = formatDate(row[data.columnMapping.data]);
            let value = row[data.columnMapping.value];
            if (typeof value === 'string') value = parseFloat(value.replace(',', '.'));
            if (!isNaN(value)) {
                if (!dailyTotals[date]) dailyTotals[date] = 0;
                dailyTotals[date] += value;
            }
        }
    });
    const dates = Object.keys(dailyTotals).sort();
    const values = dates.map(d => dailyTotals[d]);
    // Renderizar gráfico
    const ctx = document.getElementById('temporal-pdv-chart').getContext('2d');
    const canvas = ctx.canvas;
    resizeCanvasToContainer(canvas);
    if (temporalPdvChart) temporalPdvChart.destroy();
    temporalPdvChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Total de Vendas (R$)',
                data: values,
                borderColor: '#FFA500',
                backgroundColor: 'rgba(255,165,0,0.2)',
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: false,
            plugins: {
                title: {
                    display: true,
                    text: `Série Temporal de Vendas Diárias - ${pdv}`
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Data' }
                },
                y: {
                    title: { display: true, text: 'Total de Vendas (R$)' },
                    beginAtZero: true,
                    ticks: { callback: value => formatCurrency(value) }
                }
            }
        }
    });
}

// Gráfico de série temporal por SERIAL do PDV
function renderTemporalSerialChart() {
    const month = temporalMonthSelect ? temporalMonthSelect.value : null;
    const pdv = temporalPdvSelect ? temporalPdvSelect.value : null;
    if (!month || !pdv || !allData[month]) return;
    const data = allData[month];
    // Agrupar vendas por data e SERIAL para o PDV selecionado
    const serials = {};
    data.rawRows.forEach(row => {
        if (row[data.columnMapping.pdv] === pdv) {
            const serial = row[data.columnMapping.serial];
            const date = formatDate(row[data.columnMapping.data]);
            let value = row[data.columnMapping.value];
            if (typeof value === 'string') value = parseFloat(value.replace(',', '.'));
            if (!isNaN(value)) {
                if (!serials[serial]) serials[serial] = {};
                if (!serials[serial][date]) serials[serial][date] = 0;
                serials[serial][date] += value;
            }
        }
    });
    const allDates = Array.from(new Set(Object.values(serials).flatMap(obj => Object.keys(obj)))).sort();
    const datasets = Object.keys(serials).map((serial, idx) => {
        const color = SERIAL_COLORS[idx % SERIAL_COLORS.length];
        return {
            label: serial,
            data: allDates.map(date => serials[serial][date] || 0),
            borderColor: color,
            backgroundColor: color + '33',
            fill: false,
            pointRadius: 5,
            pointHoverRadius: 7
        };
    });
    // Renderizar gráfico
    const ctx = document.getElementById('temporal-serial-chart').getContext('2d');
    const canvas = ctx.canvas;
    resizeCanvasToContainer(canvas);
    if (temporalSerialChart) temporalSerialChart.destroy();
    temporalSerialChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: datasets
        },
        options: {
            responsive: false,
            plugins: {
                title: {
                    display: true,
                    text: `Série Temporal de Vendas Diárias por SERIAL - ${pdv}`
                },
                legend: {
                    position: 'right',
                    align: 'start',
                    labels: {
                        boxWidth: 18,
                        font: { size: 13 }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Data' }
                },
                y: {
                    title: { display: true, text: 'Valor Total (R$)' },
                    beginAtZero: true,
                    ticks: { callback: value => formatCurrency(value) }
                }
            }
        }
    });
}

// Função utilitária para formatar datas (YYYY-MM-DD)
function formatDate(dateStr) {
    if (!dateStr) return '';
    // Aceita datas no formato DD/MM/YYYY ou YYYY-MM-DD
    if (dateStr.includes('/')) {
        const [d, m, y] = dateStr.split(/[\/\-]/);
        return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;
    }
    return dateStr.split(' ')[0];
}

// Atualizar filtros e gráficos temporais ao carregar dados
function updateTemporalAll() {
    fillTemporalFilters();
    renderTemporalPdvChart();
    renderTemporalSerialChart();
}

// Remover event listeners dos elementos removidos
temporalMonthSelect.addEventListener('change', () => {
    updateTemporalPdvOptions();
    renderTemporalPdvChart();
    renderTemporalSerialChart();
    updatePdvStatsCards();
});
temporalPdvSelect.addEventListener('change', () => {
    renderTemporalPdvChart();
    renderTemporalSerialChart();
    updatePdvStatsCards();
});

// Atualizar os cards de estatísticas do PDV selecionado
function updatePdvStatsCards() {
    const month = temporalMonthSelect.value;
    const pdv = temporalPdvSelect.value;
    
    if (!month || !pdv || !allData[month]) {
        pdvTotalValue.textContent = formatCurrency(0);
        pdvListaValue.textContent = formatCurrency(0);
        pdvPixValue.textContent = formatCurrency(0);
        return;
    }
    
    const data = allData[month];
    let totalPdv = 0;
    let listaPdv = 0;
    let pixPdv = 0;
    
    // Calcular totais por tipo de pagamento para o PDV selecionado
    if (data.rawRows && data.columnMapping) {
        data.rawRows.forEach(row => {
            if (row[data.columnMapping.pdv] === pdv) {
                let value = row[data.columnMapping.value];
                if (typeof value === 'string') value = parseFloat(value.replace(',', '.'));
                
                if (!isNaN(value)) {
                    totalPdv += value;
                    
                    const paymentType = row[data.columnMapping.paymentType];
                    if (paymentType) {
                        const upperType = paymentType.toUpperCase();
                        if (upperType === 'LISTA') {
                            listaPdv += value;
                        } else if (upperType === 'PIX') {
                            pixPdv += value;
                        }
                    }
                }
            }
        });
    } else if (data.pdvData) {
        // Alternativa para dados agrupados ou simulados
        if (data.pdvData['LISTA'] && data.pdvData['LISTA'][pdv]) {
            listaPdv = data.pdvData['LISTA'][pdv];
            totalPdv += listaPdv;
        }
        
        if (data.pdvData['PIX'] && data.pdvData['PIX'][pdv]) {
            pixPdv = data.pdvData['PIX'][pdv];
            totalPdv += pixPdv;
        }
    }
    
    // Atualizar os valores nos cards
    pdvTotalValue.textContent = formatCurrency(totalPdv);
    pdvListaValue.textContent = formatCurrency(listaPdv);
    pdvPixValue.textContent = formatCurrency(pixPdv);
}

// Atualizar o dashboard com os dados do mês selecionado
function updateDashboard() {
    const selectedFile = monthSelect.value;
    const selectedMonth = fileToMonth[selectedFile];
    const data = allData[selectedMonth];
    
    if (data) {
        // Atualizar valor total
        totalValue.textContent = formatCurrency(data.total);
        
        // Atualizar valores de LISTA e PIX
        let listaAmount = 0;
        let pixAmount = 0;
        
        // Obter valores específicos
        for (const [type, value] of Object.entries(data.groupedData)) {
            const upperType = type.toUpperCase();
            if (upperType === 'LISTA') {
                listaAmount = value;
            } else if (upperType === 'PIX') {
                pixAmount = value;
            }
        }
        
        listaValue.textContent = formatCurrency(listaAmount);
        pixValue.textContent = formatCurrency(pixAmount);
        
        // Atualizar gráficos
        initLineChart();
        initBarChart();
        initPdvChart();
        updateTemporalAll();
        
        // Atualizar os cards de estatísticas do PDV se já houver um PDV selecionado
        updatePdvStatsCards();
        
        hideError();
    } else {
        console.warn(`Dados não disponíveis para ${selectedMonth}. Carregando dados simulados.`);
        
        // Carregar dados simulados para o mês atual
        allData[selectedMonth] = getSimulatedData(selectedMonth);
        
        // Atualizar dashboard com dados simulados
        totalValue.textContent = formatCurrency(allData[selectedMonth].total);
        listaValue.textContent = formatCurrency(allData[selectedMonth].groupedData['LISTA'] || 0);
        pixValue.textContent = formatCurrency(allData[selectedMonth].groupedData['PIX'] || 0);
        
        // Atualizar gráficos
        initLineChart();
        initBarChart();
        initPdvChart();
        updateTemporalAll();
        
        // Exibir aviso de dados simulados
        showDataNotice(`Atenção: Exibindo dados simulados para ${selectedMonth}.`);
    }
}

// Inicialização
async function initialize() {
    console.log('Inicializando dashboard...');
    showLoading();
    hideError();
    
    try {
        const success = await loadAllData();
        if (success) {
            logPdvDetails();
            updateDashboard();
            updateTemporalAll();
        } else {
            showError();
        }
    } catch (error) {
        console.error('Erro ao inicializar dashboard:', error);
        showError();
    } finally {
        hideLoading();
    }
}

// Função para exibir informações detalhadas sobre PDVs
function logPdvDetails() {
    for (const month of monthOrder) {
        const data = allData[month];
        
        if (data && data.pdvData) {
            console.log(`\n----- Detalhes para ${month} -----`);
            
            // Para cada tipo de pagamento
            for (const paymentType in data.pdvData) {
                console.log(`\nTipo de Pagamento: ${paymentType}`);
                
                // Obter PDVs ordenados por valor
                const sortedPdvs = Object.entries(data.pdvData[paymentType])
                    .sort((a, b) => b[1] - a[1]);
                
                console.log('Top 10 PDVs:');
                sortedPdvs.slice(0, 10).forEach((entry, index) => {
                    console.log(`${index + 1}. ${entry[0]}: ${formatCurrency(entry[1])}`);
                });
                
                // Calcular o total para este tipo de pagamento
                const typeTotal = sortedPdvs.reduce((sum, entry) => sum + entry[1], 0);
                console.log(`Total para ${paymentType}: ${formatCurrency(typeTotal)}`);
                
                // Exibir a quantidade total de PDVs
                console.log(`Quantidade total de PDVs para ${paymentType}: ${sortedPdvs.length}`);
            }
        }
    }
}

// Event listeners
monthSelect.addEventListener('change', updateDashboard);
retryButton.addEventListener('click', initialize);
useDemoDataButton.addEventListener('click', loadDemoData);

// Event listeners para os botões de tipo de visualização PDV (maiores/menores)
viewTopBtn.addEventListener('click', function() {
    if (currentPdvView !== 'top') {
        currentPdvView = 'top';
        viewTopBtn.classList.add('active');
        viewBottomBtn.classList.remove('active');
        initPdvChart();
    }
});

viewBottomBtn.addEventListener('click', function() {
    if (currentPdvView !== 'bottom') {
        currentPdvView = 'bottom';
        viewBottomBtn.classList.add('active');
        viewTopBtn.classList.remove('active');
        initPdvChart();
    }
});

// Event listeners para os botões de tipo de pagamento
pdvListaBtn.addEventListener('click', function() {
    if (currentPaymentType !== 'LISTA') {
        currentPaymentType = 'LISTA';
        pdvListaBtn.classList.add('active');
        pdvPixBtn.classList.remove('active');
        initPdvChart();
    }
});

pdvPixBtn.addEventListener('click', function() {
    if (currentPaymentType !== 'PIX') {
        currentPaymentType = 'PIX';
        pdvPixBtn.classList.add('active');
        pdvListaBtn.classList.remove('active');
        initPdvChart();
    }
});

// Iniciar o dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM carregado, iniciando dashboard...');
    initialize();
});

// Redimensionar gráficos ao redimensionar a janela
window.addEventListener('resize', () => {
    renderTemporalPdvChart();
    renderTemporalSerialChart();
}); 