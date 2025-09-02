// Password visibility toggle
document.getElementById('toggle-password').addEventListener('click', function() {
    const passwordInput = document.getElementById('password');
    const eyeOpen = document.getElementById('eye-open');
    const eyeClosed = document.getElementById('eye-closed');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeClosed.classList.add('hidden');
        eyeOpen.classList.remove('hidden');
    } else {
        passwordInput.type = 'password';
        eyeClosed.classList.remove('hidden');
        eyeOpen.classList.add('hidden');
    }
});

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
        // Initial status before making request
        updateLoadingStatus('Connecting to Skyward...', 5);
        
        // Create a unique session ID
        const sessionId = `${username}_${Date.now()}`;
        
        // Start polling for progress updates
        const progressInterval = setInterval(async () => {
            try {
                const progressResponse = await fetch(`/progress/${sessionId}`);
                const progressData = await progressResponse.json();
                
                if (progressData.length > 0) {
                    const latestUpdate = progressData[progressData.length - 1];
                    updateLoadingStatus(latestUpdate.message, latestUpdate.progress);
                }
            } catch (error) {
                console.log('Progress polling error:', error);
            }
        }, 500); // Poll every 500ms
        
        const response = await fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Session-ID': sessionId,
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
        });
        
        // Stop polling
        clearInterval(progressInterval);
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update status: Completing
        updateLoadingStatus('Preparing results...', 95);
        await sleep(300);
        
        // Hide loading, show results
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('results-section').classList.remove('hidden');
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        updateLoadingStatus('Error occurred: ' + error.message, 100, true);
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
            <div class="bg-gray-50 p-4 rounded-lg border-l-4 border-[#1C3764]">
                <h3 class="text-xl font-semibold text-gray-900 mb-2">Current Unweighted GPA</h3>
                <p class="text-3xl font-bold text-[#1C3764]">${currentUnweightedGPA.toFixed(2)}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg border-l-4 border-[#A23422]">
                <h3 class="text-xl font-semibold text-gray-900 mb-2">Current Weighted GPA</h3>
                <p class="text-3xl font-bold text-[#A23422]">${currentWeightedGPA.toFixed(2)}</p>
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
        if ((className.includes("AP") && !className.includes("APA")) || className.includes("Ind Study Tech Applications")) {
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
                    borderColor: '#A23422', // Alvin ISD Red
                    backgroundColor: 'rgba(162, 52, 34, 0.1)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 6,
                    pointBackgroundColor: '#A23422',
                    pointBorderColor: 'white',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#A23422',
                    pointHoverBorderColor: 'white',
                    pointHoverBorderWidth: 3
                },
                {
                    label: `Maximum GPA (${maxPossibleGPA.toFixed(2)})`,
                    data: orderedPeriods.map(period => ({
                        x: period,
                        y: maxPossibleGPA
                    })),
                    borderColor: 'rgba(28, 55, 100, 0.6)', // Skyward Blue with opacity
                    borderDash: [8, 4], // Longer dashes
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === `Maximum GPA (${maxPossibleGPA.toFixed(2)})`) {
                                return null;
                            }
                            return `GPA: ${context.parsed.y.toFixed(2)}`;
                        }
                    },
                    displayColors: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        filter: function(legendItem) {
                            return true;
                        },
                        usePointStyle: true,
                        pointStyle: 'line',
                        padding: 20,
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                }
            },
            scales: {
                y: {
                    min: yMin,
                    max: yMax,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(2);
                        },
                        font: {
                            size: 11
                        },
                        padding: 8
                    },
                    border: {
                        display: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 11
                        },
                        padding: 8
                    },
                    border: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            elements: {
                line: {
                    borderWidth: 3
                }
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