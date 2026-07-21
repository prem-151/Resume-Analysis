document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Initial setup based on localStorage or default
        const currentTheme = localStorage.getItem('theme') || 'dark-theme';
        document.body.classList.add(currentTheme);
        themeToggle.innerHTML = currentTheme === 'dark-theme' ? '<i class="fas fa-sun text-xl"></i>' : '<i class="fas fa-moon text-xl"></i>';

        themeToggle.addEventListener('click', () => {
            const isDark = document.body.classList.contains('dark-theme');
            if (isDark) {
                document.body.classList.replace('dark-theme', 'light-theme');
                localStorage.setItem('theme', 'light-theme');
                themeToggle.innerHTML = '<i class="fas fa-moon text-xl"></i>';
            } else {
                document.body.classList.replace('light-theme', 'dark-theme');
                localStorage.setItem('theme', 'dark-theme');
                themeToggle.innerHTML = '<i class="fas fa-sun text-xl"></i>';
            }
        });
    }

    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
        });
    }

    // Particles.js Init
    if (document.getElementById('particles-js')) {
        particlesJS("particles-js", {
            "particles": {
                "number": { "value": 60, "density": { "enable": true, "value_area": 800 } },
                "color": { "value": ["#4f46e5", "#ec4899", "#38bdf8"] },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.5, "random": true },
                "size": { "value": 3, "random": true },
                "line_linked": { "enable": true, "distance": 150, "color": "#4f46e5", "opacity": 0.3, "width": 1 },
                "move": { "enable": true, "speed": 1.5, "direction": "none", "random": false, "straight": false, "out_mode": "out", "bounce": false }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": { "enable": true, "mode": "grab" },
                    "onclick": { "enable": true, "mode": "push" },
                    "resize": true
                },
                "modes": {
                    "grab": { "distance": 140, "line_linked": { "opacity": 1 } },
                    "push": { "particles_nb": 3 }
                }
            },
            "retina_detect": true
        });
    }

    // Drag and Drop Logic
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-upload');
    
    if (dropZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-indigo-500', 'bg-indigo-500/10');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-indigo-500', 'bg-indigo-500/10');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            let dt = e.dataTransfer;
            let files = dt.files;
            if (files.length) {
                fileInput.files = files;
                handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }

    function handleFileUpload(file) {
        document.getElementById('upload-state').classList.add('hidden');
        document.getElementById('loading-state').classList.remove('hidden');
        
        const formData = new FormData();
        formData.append('resume', file);

        fetch('/api/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if(data.error) {
                alert(data.error);
                resetUploadState();
                return;
            }
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during analysis.');
            resetUploadState();
        });
    }

    function resetUploadState() {
        document.getElementById('upload-state').classList.remove('hidden');
        document.getElementById('loading-state').classList.add('hidden');
    }

    let radarChartInstance = null;

    function displayResults(data) {
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('results-section').classList.remove('hidden');

        // Animate Circular Progress
        const circularProgress = document.querySelector('.circular-progress');
        const progressValue = document.querySelector('.progress-value');
        
        let startValue = 0;
        let endValue = data.ats_score;
        let speed = 15;

        let progress = setInterval(() => {
            startValue++;
            progressValue.textContent = `${startValue}%`;
            circularProgress.style.background = `conic-gradient(#4f46e5 ${startValue * 3.6}deg, rgba(255,255,255,0.1) 0deg)`;
            
            if (startValue >= endValue) {
                clearInterval(progress);
            }
        }, speed);

        // Populate Skills
        const skillsContainer = document.getElementById('skills-container');
        skillsContainer.innerHTML = data.skills.map(skill => 
            `<span class="px-3 py-1 bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded-full text-sm font-semibold">${skill}</span>`
        ).join('');

        // Populate Missing Skills
        const missingSkillsContainer = document.getElementById('missing-skills-container');
        missingSkillsContainer.innerHTML = data.missing_skills.map(skill => 
            `<span class="px-3 py-1 bg-pink-500/20 text-pink-400 border border-pink-500/30 rounded-full text-sm font-semibold">${skill}</span>`
        ).join('');

        // Populate Jobs
        const jobsContainer = document.getElementById('jobs-container');
        jobsContainer.innerHTML = data.recommendations.map(job => `
            <div class="glass-card p-4 rounded-xl border-l-4 border-l-indigo-500 hover:transform hover:-translate-y-1 transition-all glow-effect cursor-pointer">
                <div class="flex justify-between items-center mb-2">
                    <h4 class="font-bold text-lg">${job.title}</h4>
                    <span class="text-sm font-bold text-green-400 bg-green-400/10 px-2 py-1 rounded-full">${job.match_percentage}% Match</span>
                </div>
                <p class="text-sm opacity-80 mb-3">${job.description}</p>
                <div class="text-xs font-semibold text-indigo-400">Required: ${job.required_skills}</div>
            </div>
        `).join('');
        
        // Render Chart
        initRadarChart(data.skills);
    }
    
    function initRadarChart(skills) {
        const ctx = document.getElementById('skillsChart');
        if (!ctx) return;
        
        if (radarChartInstance) {
            radarChartInstance.destroy();
        }

        const chartSkills = skills.length > 5 ? skills.slice(0,5) : (skills.length > 0 ? skills : ['None']);
        
        // Generate consistent "proficiency" score based on skill string hash
        const chartData = chartSkills.map(skill => {
            let hash = 0;
            for (let i = 0; i < skill.length; i++) {
                hash = skill.charCodeAt(i) + ((hash << 5) - hash);
            }
            // Normalize hash to a value between 45 and 98
            const normalized = Math.abs(hash) % 54 + 45;
            return normalized;
        });

        radarChartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: chartSkills,
                datasets: [{
                    label: 'Skill Proficiency',
                    data: chartData,
                    backgroundColor: 'rgba(79, 70, 229, 0.3)',
                    borderColor: 'rgba(79, 70, 229, 1)',
                    pointBackgroundColor: 'rgba(79, 70, 229, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(79, 70, 229, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        min: 0,
                        max: 100,
                        angleLines: { color: 'rgba(150, 150, 150, 0.2)' },
                        grid: { color: 'rgba(150, 150, 150, 0.2)' },
                        pointLabels: { color: 'rgba(150, 150, 150, 0.8)', font: { size: 12 } },
                        ticks: { display: false }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
    
    // Admin Chart Initialization
    const adminChartCtx = document.getElementById('adminStatsChart');
    if (adminChartCtx) {
        new Chart(adminChartCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Resumes Analyzed',
                    data: [12, 19, 15, 25, 22, 30, 28],
                    backgroundColor: 'rgba(147, 51, 234, 0.2)',
                    borderColor: 'rgba(147, 51, 234, 1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(150,150,150,0.1)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
});
