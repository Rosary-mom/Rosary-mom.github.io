/*
 * Gravity Engine for the Rosary round raised bed (Rosary Ridgebed / Rosarium).
 *
 * Physical scale stays linear:
 *   scaleFactor = gravityEarth / targetGravity
 *   rawHalfWidth = baseEmitterWidth * scaleFactor
 *
 * The drawn slot uses that same half-width up to SOFT_CAP_HALF (70 px).
 * Earth (10), Mars (~26) and Moon (~61) therefore look exactly as before.
 * Below about 1.4 m/s² the raw slot would eat the pipe ring (Ceres ~350 px),
 * so the drawing continues with a log and a hard cap. The readout still
 * shows the uncapped scale factor.
 */
(function () {
    var slider = document.getElementById('gravitySlider');
    var pipeCanvas = document.getElementById('pipeCanvas');
    var scaffoldCanvas = document.getElementById('scaffoldCanvas');
    if (!slider || !pipeCanvas || !scaffoldCanvas) return;

    var pipeCtx = pipeCanvas.getContext('2d');
    var scaffoldCtx = scaffoldCanvas.getContext('2d');
    var sprayCanvas = document.getElementById('sprayCanvas');
    var sprayCtx = sprayCanvas ? sprayCanvas.getContext('2d') : null;

    var gravDisplay = document.getElementById('gravityValue');
    var scaleDisplay = document.getElementById('scaleFactorValue');
    var emitterDisplay = document.getElementById('emitterValue');
    var drawLimitDisplay = document.getElementById('drawLimitValue');
    var systemStatus = document.getElementById('systemStatus');
    var presetButtons = document.querySelectorAll('.preset-btn');

    var envName = document.getElementById('envName');
    var envGravity = document.getElementById('envGravity');
    var envPressure = document.getElementById('envPressure');
    var envTemperature = document.getElementById('envTemperature');
    var envWater = document.getElementById('envWater');
    var envHypothesis = document.getElementById('envHypothesis');
    var envSource = document.getElementById('envSource');
    var habitatToggle = document.getElementById('habitatToggle');
    var habitatBtn = document.getElementById('habitatBtn');
    var vacuumBtn = document.getElementById('vacuumBtn');
    var sprayCaption = document.getElementById('sprayCaption');

    var canvasSize = 400;
    var center = canvasSize / 2;
    var gravityEarth = 9.81;
    var baseEmitterWidth = 10;
    var outerRadius = 160;
    var innerRadius = 120;
    var SOFT_CAP_HALF = 70;
    var HARD_CAP_HALF = 92;

    var targetGravity = 9.81;
    var activeEnv = 'earth';
    var ceresMode = 'habitat';

    var ENVIRONMENTS = {
        earth: {
            label: 'Erde',
            g: 9.81,
            gravityText: '9,81 m/s² (Simulation; Normfallbeschleunigung 9,80665)',
            pressureText: '1014 mbar auf Meereshöhe',
            temperatureText: 'Mittel 288 K, typisch 283–293 K',
            waterText: 'Flüssiges Wasser ist an der Oberfläche stabil.',
            hypothesis: '',
            source: 'Quelle: NASA Goddard, Earth Fact Sheet (NSSDCA). Mittlere Schwere 9,82 m/s², Oberflächendruck 1014 mbar, Mitteltemperatur 288 K, Tagesgang 283–293 K. https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html'
        },
        mars: {
            label: 'Mars',
            g: 3.72,
            gravityText: '3,72 m/s² (Simulation; NASA-Mittel 3,73)',
            pressureText: '6,36 mbar, je nach Jahreszeit etwa 4,0–8,7 mbar',
            temperatureText: 'Mittel etwa 214 K, typisch 184–242 K',
            waterText: 'Der Druck liegt nahe am Tripelpunkt des Wassers. Freies Wasser bleibt kaum flüssig.',
            hypothesis: '',
            source: 'Quelle: NASA Goddard, Mars Fact Sheet (NSSDCA). Mittlere Oberflächenschwere 3,73 m/s², Druck 6,36 mbar am mittleren Radius, Mitteltemperatur etwa 214 K, Tagesgang am Viking-1-Landeplatz 184–242 K. https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html'
        },
        moon: {
            label: 'Mond',
            g: 1.62,
            gravityText: '1,62 m/s²',
            pressureText: '3×10⁻¹⁵ bar nachts (Exosphäre)',
            temperatureText: '95–390 K am Äquator',
            waterText: 'Keine tragende Atmosphäre. Die Strahlgrafik zeigt nur die Flugbahn, nicht eine stabile Flüssigkeit.',
            hypothesis: '',
            source: 'Quelle: NASA Goddard, Moon Fact Sheet (NSSDCA). Oberflächenschwere 1,62 m/s², nächtlicher Druck 3×10⁻¹⁵ bar, äquatorialer Tagesgang 95–390 K. https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html'
        },
        ceres: {
            label: 'Ceres',
            g: 0.28,
            gravityText: '0,28 m/s² (≈ 0,029 g; äquatorial 0,284)',
            pressureText: 'praktisch Vakuum; nur eine vorübergehende, extrem dünne Wasserdampf-Exosphäre',
            temperatureText: 'ca. 110–155 K',
            waterText: 'Offenes Wasser siedet, gefriert und sublimiert. Ein Teich hält an der Oberfläche nicht.',
            hypothesis: 'Hypothese/Konzept: Auf Ceres funktioniert die Düse und der Teich nur in einem druckbeaufschlagten, beheizten Gewächshaus- bzw. Habitat-Dom.',
            source: 'Quellen: Schwere gerundet auf 0,28 m/s² (0,029 g). Äquatorial 0,284 m/s² aus dem Dawn-Schwerefeld (NASA/JPL Dawn, Park u. a.). Temperatur 110–155 K: Castillo-Rogez, Raymond, Russell und das Dawn-Team, „Dawn at Ceres: What Have We Learned?“, NASA/JPL 2017. Atmosphäre: NASA Science, Ceres Facts — sehr dünn, mit Wasserdampf durch Sublimation oder Eisvulkane; JPL/Dawn — vorübergehende Exosphäre, an Sonnenaktivität gekoppelt. Örtliche Maxima können etwa 235 K erreichen (Tosi u. a. 2015, Dawn). https://science.nasa.gov/dwarf-planets/ceres/facts/ · https://www.jpl.nasa.gov/news/ceres-temporary-atmosphere-linked-to-solar-activity'
        }
    };

    function de(n, digits) {
        return n.toFixed(digits).replace('.', ',');
    }

    function emitterGeometry(g) {
        var safeG = Math.max(g, 0.05);
        var scaleFactor = gravityEarth / safeG;
        var rawHalf = baseEmitterWidth * scaleFactor;
        var drawnHalf = rawHalf;
        var limited = false;
        if (rawHalf > SOFT_CAP_HALF) {
            limited = true;
            drawnHalf = SOFT_CAP_HALF + 16 * Math.log10(rawHalf / SOFT_CAP_HALF);
        }
        if (drawnHalf > HARD_CAP_HALF) {
            drawnHalf = HARD_CAP_HALF;
            limited = true;
        }
        return {
            scaleFactor: scaleFactor,
            rawHalf: rawHalf,
            drawnHalf: drawnHalf,
            limited: limited
        };
    }

    function matchPreset(g) {
        var ids = Object.keys(ENVIRONMENTS);
        for (var i = 0; i < ids.length; i++) {
            if (Math.abs(g - ENVIRONMENTS[ids[i]].g) < 0.001) return ids[i];
        }
        return 'custom';
    }

    function isVacuumSurface() {
        return activeEnv === 'ceres' && ceresMode === 'vacuum';
    }

    function setStatus(text, color) {
        if (!systemStatus) return;
        systemStatus.textContent = text;
        systemStatus.style.color = color;
    }

    function updateEnvironmentPanel() {
        var vacuum = isVacuumSurface();
        if (activeEnv === 'custom') {
            if (envName) envName.textContent = 'Benutzerdefiniert';
            if (envGravity) envGravity.textContent = de(targetGravity, 2) + ' m/s²';
            if (envPressure) envPressure.textContent = 'kein Katalogwert';
            if (envTemperature) envTemperature.textContent = 'kein Katalogwert';
            if (envWater) envWater.textContent = 'Die Auslass-Skalierung folgt nur der eingestellten Schwere.';
            if (envHypothesis) {
                envHypothesis.textContent = '';
                envHypothesis.classList.remove('is-visible');
            }
            if (envSource) envSource.textContent = 'Kein Katalogkörper. Erde, Mars, Mond und Ceres setzen Druck und Temperatur aus den genannten Quellen.';
        } else {
            var env = ENVIRONMENTS[activeEnv];
            if (envName) envName.textContent = env.label;
            if (envGravity) envGravity.textContent = env.gravityText;
            if (envPressure) envPressure.textContent = env.pressureText;
            if (envTemperature) envTemperature.textContent = env.temperatureText;
            if (envWater) envWater.textContent = env.waterText;
            if (envHypothesis) {
                envHypothesis.textContent = env.hypothesis;
                envHypothesis.classList.toggle('is-visible', !!env.hypothesis);
            }
            if (envSource) envSource.textContent = env.source;
        }

        if (habitatToggle) {
            habitatToggle.classList.toggle('is-visible', activeEnv === 'ceres');
        }
        if (habitatBtn && vacuumBtn) {
            habitatBtn.classList.toggle('active', ceresMode === 'habitat');
            vacuumBtn.classList.toggle('active', ceresMode === 'vacuum');
            habitatBtn.setAttribute('aria-pressed', ceresMode === 'habitat' ? 'true' : 'false');
            vacuumBtn.setAttribute('aria-pressed', ceresMode === 'vacuum' ? 'true' : 'false');
        }

        if (vacuum) setStatus('SUBLIMATION', '#ffb020');
        else if (activeEnv === 'ceres') setStatus('HABITAT', '#7ee0ff');
        else setStatus('NOMINAL', '#0f0');

        if (sprayCaption) {
            if (vacuum) {
                sprayCaption.textContent = 'Offene Oberfläche: Der Strahl gefriert und sublimiert. Kein stabiler Teich.';
            } else if (activeEnv === 'ceres') {
                sprayCaption.textContent = 'Im Druck-Habitat: flüssiger Strahl bei Ceres-Schwere, weiter Wurf, Teich bleibt.';
            } else if (activeEnv === 'moon') {
                sprayCaption.textContent = 'Nur die Flugbahn. An der offenen Mondoberfläche fehlt eine Atmosphäre.';
            } else if (activeEnv === 'custom') {
                sprayCaption.textContent = 'Benutzerdefinierte Schwere. Die Grafik zeigt die Flugbahn ohne Katalog-Phasenwechsel.';
            } else {
                sprayCaption.textContent = 'Flüssiger Düsenstrahl. Die Fallzeit folgt der eingestellten Schwere.';
            }
        }
    }

    function drawGenCAD() {
        var geo = emitterGeometry(targetGravity);
        var dynamicEmitterWidth = geo.drawnHalf;

        if (gravDisplay) gravDisplay.textContent = de(targetGravity, 2) + ' m/s²';
        if (scaleDisplay) scaleDisplay.textContent = de(geo.scaleFactor, 2);
        if (emitterDisplay) emitterDisplay.textContent = String(Math.round(dynamicEmitterWidth * 2));
        if (drawLimitDisplay) {
            drawLimitDisplay.textContent = geo.limited
                ? 'log (Roh-Halbbreite ' + de(geo.rawHalf, 0) + ' px)'
                : 'aus';
        }

        pipeCtx.clearRect(0, 0, canvasSize, canvasSize);
        pipeCtx.fillStyle = '#ffffff';
        pipeCtx.fillRect(0, 0, canvasSize, canvasSize);

        pipeCtx.fillStyle = '#111';
        pipeCtx.beginPath();
        pipeCtx.arc(center, center, outerRadius, 0, Math.PI * 2);
        pipeCtx.fill();

        pipeCtx.globalCompositeOperation = 'destination-out';
        pipeCtx.beginPath();
        pipeCtx.arc(center, center, innerRadius, 0, Math.PI * 2);
        pipeCtx.fill();
        pipeCtx.fillRect(center - dynamicEmitterWidth, 0, dynamicEmitterWidth * 2, canvasSize);
        pipeCtx.fillRect(0, center - dynamicEmitterWidth, canvasSize, dynamicEmitterWidth * 2);
        pipeCtx.globalCompositeOperation = 'source-over';

        scaffoldCtx.clearRect(0, 0, canvasSize, canvasSize);
        scaffoldCtx.fillStyle = '#ffffff';
        scaffoldCtx.fillRect(0, 0, canvasSize, canvasSize);
        scaffoldCtx.strokeStyle = '#333';
        scaffoldCtx.lineWidth = 6;
        var gridSpacing = 40;
        scaffoldCtx.beginPath();
        for (var x = 0; x <= canvasSize; x += gridSpacing) {
            scaffoldCtx.moveTo(x, 0);
            scaffoldCtx.lineTo(x, canvasSize);
        }
        for (var y = 0; y <= canvasSize; y += gridSpacing) {
            scaffoldCtx.moveTo(0, y);
            scaffoldCtx.lineTo(canvasSize, y);
        }
        scaffoldCtx.stroke();

        scaffoldCtx.globalCompositeOperation = 'destination-out';
        scaffoldCtx.beginPath();
        scaffoldCtx.arc(center, center, outerRadius + 8, 0, Math.PI * 2);
        scaffoldCtx.fill();
        scaffoldCtx.globalCompositeOperation = 'source-over';

        updateEnvironmentPanel();
    }

    function setGravity(value, envId) {
        targetGravity = value;
        slider.value = String(value);
        activeEnv = envId || matchPreset(value);
        presetButtons.forEach(function (btn) {
            btn.classList.toggle('active', btn.getAttribute('data-env') === activeEnv);
        });
        drawGenCAD();
    }

    slider.addEventListener('input', function () {
        var value = parseFloat(slider.value);
        if (!isFinite(value)) return;
        targetGravity = value;
        activeEnv = matchPreset(value);
        presetButtons.forEach(function (btn) {
            btn.classList.toggle('active', btn.getAttribute('data-env') === activeEnv);
        });
        drawGenCAD();
    });

    presetButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = btn.getAttribute('data-env');
            var env = ENVIRONMENTS[id];
            if (!env) return;
            setGravity(env.g, id);
        });
    });

    if (habitatBtn) {
        habitatBtn.addEventListener('click', function () {
            ceresMode = 'habitat';
            drawGenCAD();
        });
    }
    if (vacuumBtn) {
        vacuumBtn.addEventListener('click', function () {
            ceresMode = 'vacuum';
            if (activeEnv !== 'ceres') setGravity(ENVIRONMENTS.ceres.g, 'ceres');
            else drawGenCAD();
        });
    }

    var drops = [];
    var ripples = [];
    var sprayWidth = sprayCanvas ? sprayCanvas.width : 720;
    var sprayHeight = sprayCanvas ? sprayCanvas.height : 300;
    var nozzleX = 86;
    var nozzleY = 168;
    var lastStamp = 0;
    var spawnAcc = 0;
    var stars = [];
    for (var s = 0; s < 28; s++) {
        stars.push({
            x: (s * 97) % sprayWidth,
            y: (s * 53) % 150,
            r: (s % 3) + 0.6
        });
    }

    function spawnDrop() {
        var vacuum = isVacuumSurface();
        var aim = vacuum ? 0.22 : 0.28;
        var angle = aim + (Math.random() - 0.35) * 0.42;
        var speed = 150 + Math.random() * 50;
        drops.push({
            x: nozzleX,
            y: nozzleY + (Math.random() - 0.5) * 8,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            age: 0,
            r: 2.1 + Math.random() * 1.7,
            ice: 0
        });
        if (drops.length > 90) drops.shift();
    }

    function drawSpray(dt) {
        if (!sprayCtx) return;
        var vacuum = isVacuumSurface();
        var gRatio = Math.max(targetGravity, 0.05) / gravityEarth;
        var ay = 280 * gRatio;

        spawnAcc += dt;
        var interval = vacuum ? 0.045 : 0.038;
        while (spawnAcc >= interval) {
            spawnDrop();
            spawnAcc -= interval;
        }

        sprayCtx.clearRect(0, 0, sprayWidth, sprayHeight);
        if (vacuum) {
            sprayCtx.fillStyle = '#05070c';
            sprayCtx.fillRect(0, 0, sprayWidth, sprayHeight);
            for (var i = 0; i < stars.length; i++) {
                sprayCtx.fillStyle = 'rgba(255,255,255,0.75)';
                sprayCtx.beginPath();
                sprayCtx.arc(stars[i].x, stars[i].y, stars[i].r, 0, Math.PI * 2);
                sprayCtx.fill();
            }
        } else {
            var sky = sprayCtx.createLinearGradient(0, 0, 0, sprayHeight);
            sky.addColorStop(0, '#10202c');
            sky.addColorStop(1, '#1a3040');
            sprayCtx.fillStyle = sky;
            sprayCtx.fillRect(0, 0, sprayWidth, sprayHeight);
            sprayCtx.strokeStyle = 'rgba(212,175,55,0.45)';
            sprayCtx.lineWidth = 2;
            sprayCtx.beginPath();
            sprayCtx.moveTo(20, sprayHeight - 8);
            sprayCtx.quadraticCurveTo(sprayWidth / 2, 18, sprayWidth - 20, sprayHeight - 8);
            sprayCtx.stroke();
        }

        var pondY = sprayHeight - 36;
        if (vacuum) {
            sprayCtx.strokeStyle = 'rgba(200,220,230,0.45)';
            sprayCtx.setLineDash([5, 5]);
            sprayCtx.lineWidth = 2;
            sprayCtx.beginPath();
            sprayCtx.ellipse(470, pondY + 8, 150, 16, 0, 0, Math.PI * 2);
            sprayCtx.stroke();
            sprayCtx.setLineDash([]);
            sprayCtx.fillStyle = 'rgba(220,230,235,0.8)';
            sprayCtx.font = '13px sans-serif';
            sprayCtx.fillText('kein Teich', 432, pondY - 14);
        } else {
            sprayCtx.fillStyle = 'rgba(0, 170, 220, 0.82)';
            sprayCtx.beginPath();
            sprayCtx.ellipse(430, pondY + 6, 150, 18, 0, 0, Math.PI * 2);
            sprayCtx.fill();
            sprayCtx.fillStyle = 'rgba(220,245,255,0.9)';
            sprayCtx.font = '13px sans-serif';
            sprayCtx.fillText('Teich', 412, pondY - 16);
        }

        sprayCtx.fillStyle = '#c8b27a';
        sprayCtx.beginPath();
        sprayCtx.moveTo(46, nozzleY - 16);
        sprayCtx.lineTo(nozzleX, nozzleY - 7);
        sprayCtx.lineTo(nozzleX, nozzleY + 7);
        sprayCtx.lineTo(46, nozzleY + 16);
        sprayCtx.closePath();
        sprayCtx.fill();

        for (var d = drops.length - 1; d >= 0; d--) {
            var p = drops[d];
            p.age += dt;
            p.vy += ay * dt;
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            if (vacuum) {
                var freezeAt = 0.16;
                if (p.age > freezeAt) {
                    p.ice = Math.min(1, (p.age - freezeAt) / 0.55);
                }
            }
            var gone = p.x > sprayWidth + 20 || p.y > sprayHeight + 20 || p.x < -20;
            var sublimated = vacuum && p.ice >= 1;
            var landed = !vacuum && p.y >= pondY && p.x > 250 && p.x < 620 && p.vy > 0;
            if (sublimated || gone) {
                drops.splice(d, 1);
                continue;
            }
            if (landed) {
                ripples.push({ x: p.x, y: pondY + 6, age: 0 });
                if (ripples.length > 14) ripples.shift();
                drops.splice(d, 1);
                continue;
            }
            var ice = vacuum ? p.ice : 0;
            var radius = p.r * (1 - ice * 0.7);
            var alpha = 1 - ice * 0.92;
            var red = Math.round(40 + ice * 210);
            var green = Math.round(190 + ice * 55);
            var blue = Math.round(255 - ice * 15);
            sprayCtx.fillStyle = 'rgba(' + red + ',' + green + ',' + blue + ',' + alpha.toFixed(3) + ')';
            sprayCtx.beginPath();
            sprayCtx.arc(p.x, p.y, Math.max(0.4, radius), 0, Math.PI * 2);
            sprayCtx.fill();
            if (ice > 0.25) {
                sprayCtx.fillStyle = 'rgba(230,240,245,' + (ice * 0.35).toFixed(3) + ')';
                sprayCtx.beginPath();
                sprayCtx.arc(p.x, p.y - 7 * ice, 5 * ice, 0, Math.PI * 2);
                sprayCtx.fill();
            }
        }

        for (var r = ripples.length - 1; r >= 0; r--) {
            ripples[r].age += dt;
            if (ripples[r].age > 0.8) {
                ripples.splice(r, 1);
                continue;
            }
            var u = ripples[r].age / 0.8;
            sprayCtx.strokeStyle = 'rgba(210,245,255,' + (1 - u).toFixed(3) + ')';
            sprayCtx.lineWidth = 1.5;
            sprayCtx.beginPath();
            sprayCtx.ellipse(ripples[r].x, ripples[r].y, 6 + u * 22, 3 + u * 6, 0, 0, Math.PI * 2);
            sprayCtx.stroke();
        }

        sprayCtx.fillStyle = vacuum ? '#ffd7a1' : '#d7f6ff';
        sprayCtx.font = '14px sans-serif';
        sprayCtx.fillText(vacuum ? 'Offene Oberfläche · Sublimation' : 'Druck-Habitat · flüssiger Strahl', 16, 26);
    }

    function frame(stamp) {
        if (!lastStamp) lastStamp = stamp;
        var dt = Math.min(0.05, (stamp - lastStamp) / 1000);
        lastStamp = stamp;
        drawSpray(dt);
        window.requestAnimationFrame(frame);
    }

    setGravity(9.81, 'earth');
    if (sprayCtx) window.requestAnimationFrame(frame);
})();
