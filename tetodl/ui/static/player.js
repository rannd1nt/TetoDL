document.addEventListener('DOMContentLoaded', function() {
    const media = document.getElementById('mediaElement');
    const playBtn = document.getElementById('playBtn');
    const progressBar = document.getElementById('progressBar');
    const currTime = document.getElementById('currTime');
    const totalTime = document.getElementById('totalTime');
    const cover = document.getElementById('mediaCover');
    const playIcon = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none" width="24" height="24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
    const pauseIcon = '<svg viewBox="0 0 24 24" fill="currentColor" stroke="none" width="24" height="24"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';

    if(!media) return;

    function togglePlay() {
        if (media.paused) {
            media.play();
            playBtn.innerHTML = pauseIcon;
            if(cover) cover.classList.add('playing');
        } else {
            media.pause();
            playBtn.innerHTML = playIcon;
            if(cover) cover.classList.remove('playing');
        }
    }
    playBtn.addEventListener('click', togglePlay);

    function updateSliderFill(value) {
        progressBar.style.backgroundSize = value + '% 100%';
    }

    media.addEventListener('timeupdate', function() {
        if(media.duration) {
            const percent = (media.currentTime / media.duration) * 100;
            progressBar.value = percent;
            
            updateSliderFill(percent);
            
            currTime.innerText = formatTime(media.currentTime);
            totalTime.innerText = formatTime(media.duration);
        }
    });

    progressBar.addEventListener('input', function() {
        updateSliderFill(this.value);
        
        if(media.duration) {
            const seekTime = (this.value / 100) * media.duration;
            media.currentTime = seekTime;
        }
    });

    function formatTime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        
        const sStr = (s < 10 ? '0' : '') + s;
        
        if (h > 0) {
            const mStr = (m < 10 ? '0' : '') + m;
            return h + ':' + mStr + ':' + sStr;
        } else {
            return m + ':' + sStr;
        }
    }

    media.play().then(() => {
        playBtn.innerHTML = pauseIcon;
        if(cover) cover.classList.add('playing');
    }).catch(() => {
        playBtn.innerHTML = playIcon;
    });
    
    if(media.tagName === 'VIDEO') {
        media.addEventListener('click', togglePlay);
    }
});

function filterList() {
    const input = document.getElementById('searchInput');
    if (!input) return;
    const filter = input.value.toLowerCase();
    const li = document.getElementsByClassName('file-item');

    for (let i = 0; i < li.length; i++) {
        if (li[i].classList.contains('parent-dir')) continue;
        const nameSpan = li[i].getElementsByClassName("name")[0];
        if (nameSpan) {
            const txtValue = nameSpan.textContent || nameSpan.innerText;
            if (txtValue.toLowerCase().indexOf(filter) > -1) {
                li[i].style.display = "";
            } else {
                li[i].style.display = "none";
            }
        }
    }
}
