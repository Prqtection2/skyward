document.getElementById('login-btn').addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        alert('Please enter both username and password');
        return;
    }
    
    // Show loading section, hide others
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('loading-section').classList.remove('hidden');
    document.getElementById('results-section').classList.add('hidden');

    const statusElement = document.getElementById('status-message');
    const progressBar = document.getElementById('progress-bar');
    
    try {
        // Update status: Logging in
        updateLoadingStatus('Logging into Skyward...', 20);
        
        const response = await fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
        });
        
        // Update status: Processing grades
        updateLoadingStatus('Accessing gradebook...', 40);
        await sleep(1000); // Small delay for visual feedback
        
        updateLoadingStatus('Extracting grades...', 60);
        await sleep(1000);
        
        updateLoadingStatus('Calculating GPAs...', 80);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update status: Completing
        updateLoadingStatus('Preparing results...', 90);
        await sleep(500);
        
        // Hide loading, show results
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('results-section').classList.remove('hidden');
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        updateLoadingStatus('Error: ' + error.message, 100, true);
        await sleep(2000);
        
        // Show login section again on error
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('login-section').classList.remove('hidden');
        alert('Error: ' + error.message);
    }
});

function updateLoadingStatus(message, progress, isError = false) {
    const statusElement = document.getElementById('status-message');
    const progressBar = document.getElementById('progress-bar');
    
    statusElement.textContent = message;
    if (isError) {
        statusElement.classList.add('text-red-500');
        progressBar.classList.remove('bg-blue-500');
        progressBar.classList.add('bg-red-500');
    }
    progressBar.style.width = `${progress}%`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function displayResults(data) {
    // Get ordered periods from the first class (assuming all classes have same period order)
    const firstClass = Object.values(data.grades)[0];
    const orderedPeriods = Object.keys(firstClass);

    // Create grades table
    const gradesTable = createGradesTable(data.grades, orderedPeriods);
    document.getElementById('grades-table').innerHTML = gradesTable;
    
    // Get current (most recent) GPAs
    const currentUnweightedGPA = data.unweighted_gpas[orderedPeriods[orderedPeriods.length - 1]];
    const currentWeightedGPA = data.weighted_gpas[orderedPeriods[orderedPeriods.length - 1]];

    // Create current GPA section
    const currentGPAHtml = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <div class="bg-blue-50 p-4 rounded-lg">
                <h3 class="text-xl font-semibold text-gray-900 mb-2">Current Unweighted GPA</h3>
                <p class="text-3xl font-bold text-blue-600">${currentUnweightedGPA.toFixed(2)}</p>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg">
                <h3 class="text-xl font-semibold text-gray-900 mb-2">Current Weighted GPA</h3>
                <p class="text-3xl font-bold text-purple-600">${currentWeightedGPA.toFixed(2)}</p>
            </div>
        </div>
    `;
    document.getElementById('current-gpa').innerHTML = currentGPAHtml;
    
    // Create GPA tables
    const unweightedTable = createGPATable(data.unweighted_gpas, orderedPeriods);
    document.getElementById('unweighted-table').innerHTML = unweightedTable;
    
    const weightedTable = createGPATable(data.weighted_gpas, orderedPeriods);
    document.getElementById('weighted-table').innerHTML = weightedTable;

    // Make sure login section is hidden and results section is shown
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('results-section').classList.remove('hidden');
}

function createGradesTable(grades, orderedPeriods) {
    if (!grades || Object.keys(grades).length === 0) {
        return '<p class="text-gray-500">No grades available</p>';
    }

    return `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Class
                    </th>
                    ${orderedPeriods.map(period => `
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            ${period}
                        </th>
                    `).join('')}
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                ${Object.entries(grades).map(([className, classGrades]) => `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${className}
                        </td>
                        ${orderedPeriods.map(period => `
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${classGrades[period] ? classGrades[period].toFixed(1) : '-'}
                            </td>
                        `).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function createGPATable(gpas, orderedPeriods) {
    if (!gpas || Object.keys(gpas).length === 0) {
        return '<p class="text-gray-500">No GPA data available</p>';
    }

    return `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Period
                    </th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        GPA
                    </th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                ${orderedPeriods.map(period => `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${period}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            ${gpas[period].toFixed(2)}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
} 