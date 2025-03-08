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
        
        updateLoadingStatus('Extracting grades...', 60);
        
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
        return;
    }
    progressBar.style.width = `${progress}%`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function displayResults(data) {
    // First thing: manage visibility
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');
    document.getElementById('results-section').classList.remove('hidden');

    // Debug logging
    console.log('Raw data from Python:', data);
    console.log('Ordered Periods from Python:', data.ordered_periods);
    console.log('Grades:', data.grades);
    console.log('Unweighted GPAs:', data.unweighted_gpas);
    console.log('Weighted GPAs:', data.weighted_gpas);

    // Use the ordered periods from Python
    const orderedPeriods = data.ordered_periods;
    console.log('Periods being used for display:', orderedPeriods);

    // Create grades table
    const gradesTable = createGradesTable(data.grades, orderedPeriods);
    document.getElementById('grades-table').innerHTML = gradesTable;
    
    // Get current (most recent) GPAs with fallback
    // Find the last period that has a GPA value
    const currentPeriod = [...orderedPeriods]
        .reverse()
        .find(period => data.unweighted_gpas[period] !== undefined);
    console.log('Current period:', currentPeriod);
    const currentUnweightedGPA = data.unweighted_gpas[currentPeriod] || 0;
    const currentWeightedGPA = data.weighted_gpas[currentPeriod] || 0;
    console.log('Current GPAs:', { unweighted: currentUnweightedGPA, weighted: currentWeightedGPA });

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

    // Add graph
    const ctx = document.getElementById('weighted-chart').getContext('2d');
    const weightedGPAs = orderedPeriods
        .filter(period => data.weighted_gpas[period] !== undefined)
        .map(period => ({
            x: period,
            y: data.weighted_gpas[period]
        }));

    // Calculate maximum possible GPA based on actual class composition
    const maxPossibleGPA = Object.keys(data.grades).reduce((sum, className) => {
        if (className.includes("AP") && !className.includes("APA")) {
            return sum + 8.0;  // AP class
        } else if (className.includes("APA")) {
            return sum + 7.0;  // APA class
        }
        return sum + 6.0;  // Regular class
    }, 0) / Object.keys(data.grades).length;  // Divide by total number of classes

    // Calculate y-axis bounds based on current GPA and maximum possible GPA
    const yMin = Math.floor(currentWeightedGPA - 0.5); // Round down to nearest whole number
    const maxValue = Math.max(...weightedGPAs.map(gpa => gpa.y), maxPossibleGPA);
    const yMax = Math.ceil(maxValue * 10) / 10; // Round up to nearest 0.1

    new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Weighted GPA',
                    data: weightedGPAs,
                    borderColor: 'rgb(147, 51, 234)',
                    backgroundColor: 'rgba(147, 51, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: `Maximum GPA (${maxPossibleGPA.toFixed(2)})`,
                    data: orderedPeriods.map(period => ({
                        x: period,
                        y: maxPossibleGPA
                    })),
                    borderColor: 'rgba(239, 68, 68, 0.5)', // More transparent red
                    borderDash: [5, 5], // Dotted line
                    borderWidth: 1, // Thinner line
                    pointRadius: 0, // Hide points
                    fill: false,
                    order: 1 // Put this dataset behind the GPA line
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === `Maximum GPA (${maxPossibleGPA.toFixed(2)})`) {
                                return null; // Don't show max GPA in tooltip
                            }
                            return `GPA: ${context.parsed.y.toFixed(2)}`;
                        }
                    },
                    displayColors: false, // Remove color boxes in tooltip
                    backgroundColor: 'rgba(0, 0, 0, 0.7)', // Semi-transparent background
                    padding: 8,
                    titleFont: {
                        size: 12
                    },
                    bodyFont: {
                        size: 12
                    }
                },
                legend: {
                    display: true,
                    labels: {
                        filter: function(legendItem) {
                            return true; // Show both labels now
                        },
                        usePointStyle: true,
                        pointStyle: 'line'
                    }
                }
            },
            scales: {
                y: {
                    min: yMin,
                    max: yMax,
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

function createGradesTable(grades, orderedPeriods) {
    console.log('Creating grades table with periods:', orderedPeriods);
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
    console.log('Creating GPA table with periods:', orderedPeriods);
    console.log('GPA data:', gpas);
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
                ${orderedPeriods.map(period => {
                    // Only create a row if the GPA exists for this period
                    if (gpas[period] !== undefined) {
                        return `
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    ${period}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    ${gpas[period].toFixed(2)}
                                </td>
                            </tr>
                        `;
                    }
                    return ''; // Skip periods with no GPA
                }).join('')}
            </tbody>
        </table>
    `;
} 