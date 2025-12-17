let ws;
let localStream;
let peerConnection;
let recognition;
let isListening = false;
let currentAudio = null;
let isAIMainView = true; // true = AI main, false = User main

// WebSocket connection
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === 'ai_response') {
            addMessage('AI', data.content, 'ai');

            if (data.audio) {
                playAudio(data.audio);
            }
        } else if (data.type === 'webrtc_answer') {
            handleWebRTCAnswer(data.sdp);
        }
    };

    ws.onclose = function (event) {
        addMessage('System', 'Backend disconnected. Session ended.', 'ai');
        endSession();
    };

    ws.onerror = function (error) {
        addMessage('System', 'Connection error. Please restart the backend.', 'ai');
        endSession();
    };
}

// Play server-side generated audio
function playAudio(audioBase64) {
    if (!audioBase64) return;

    // Stop previous
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }

    // Create audio from base64
    currentAudio = new Audio("data:audio/wav;base64," + audioBase64);

    // Handle animation
    currentAudio.onplay = function () {
        updateVoiceStatus('🔊 AI Speaking...');
        animateAIAvatar(true);
    };

    currentAudio.onend = function () {
        updateVoiceStatus('🎤 Always Listening (can interrupt)');
        animateAIAvatar(false);
        currentAudio = null;
    };

    currentAudio.onerror = function (e) {
        console.error("Audio playback error", e);
        updateVoiceStatus('❌ Audio Error');
        currentAudio = null;
    };

    // Play
    currentAudio.play().catch(e => console.error("Auto-play blocked", e));
}

// ChatGPT-like voice recognition with better reliability
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function () {
            updateVoiceStatus('🎤 Listening...');
        };

        recognition.onresult = function (event) {
            let transcript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    transcript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            transcript = transcript.trim();
            if (transcript.length > 0) {
                // Stop AI if it's currently speaking (interruption)
                if (currentAudio) {
                    currentAudio.pause();
                    currentAudio = null;
                    animateAIAvatar(false);
                    updateVoiceStatus('🛑 Interrupted AI');
                }

                updateVoiceStatus('Processing...');
                addMessage('You', transcript, 'user');


                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'voice_message',
                        content: transcript
                    }));
                } else {
                    addMessage('System', 'Connection lost. Please restart session.', 'ai');
                }
            }
        };

        recognition.onerror = function (event) {
            console.log('Speech recognition error:', event.error);
            updateVoiceStatus('❌ Error: ' + event.error);

            // Auto-retry on certain errors
            if (event.error === 'no-speech' || event.error === 'audio-capture') {
                setTimeout(() => {
                    if (!currentAudio) {
                        startListening();
                    }
                }, 2000);
            }
        };

        recognition.onend = function () {
            isListening = false;
            updateVoiceStatus('🔄 Restarting...');

            // Immediately restart for continuous listening
            setTimeout(() => {
                if (document.getElementById('sessionActive').style.display !== 'none') {
                    startListening();
                }
            }, 300);
        };
    } else {
        addMessage('System', 'Voice recognition not supported. Use Chrome/Edge browser.', 'ai');
    }
}

// Update voice status display
function updateVoiceStatus(status) {
    const statusDiv = document.getElementById('voiceStatus');
    if (statusDiv) {
        statusDiv.textContent = status;
    }
}

// Switch between AI main view and User main view
function switchView() {
    const aiMainView = document.getElementById('aiMainView');
    const userMainView = document.getElementById('userMainView');
    const aiPipView = document.getElementById('aiPipView');
    const userPipView = document.getElementById('userPipView');
    const mainLabel = document.getElementById('mainLabel');

    if (isAIMainView) {
        // Switch to User main view
        aiMainView.style.display = 'none';
        userMainView.style.display = 'block';
        aiPipView.style.display = 'flex';
        userPipView.style.display = 'none';
        mainLabel.textContent = 'You';

        // Connect user video to main view
        if (localStream) {
            userMainView.srcObject = localStream;
        }

        isAIMainView = false;
    } else {
        // Switch to AI main view
        aiMainView.style.display = 'flex';
        userMainView.style.display = 'none';
        aiPipView.style.display = 'none';
        userPipView.style.display = 'block';
        mainLabel.textContent = 'AI Assistant';

        // Connect user video to PIP view
        if (localStream) {
            userPipView.srcObject = localStream;
        }

        isAIMainView = true;
    }
}

// Animate AI avatar
function animateAIAvatar(speaking) {
    const avatar = document.querySelector('.ai-avatar');
    const pipAvatar = document.querySelector('.pip-ai-avatar');

    if (avatar) {
        if (speaking) {
            avatar.classList.add('speaking');
        } else {
            avatar.classList.remove('speaking');
        }
    }

    if (pipAvatar) {
        if (speaking) {
            pipAvatar.style.animation = 'aiTalking 1.5s ease-in-out infinite';
        } else {
            pipAvatar.style.animation = 'none';
        }
    }
}

// Start listening function with better error handling
function startListening() {
    if (!recognition) {
        updateVoiceStatus('❌ Voice not supported');
        return;
    }

    if (isListening) {
        return; // Already listening
    }

    try {
        recognition.start();
        isListening = true;
    } catch (error) {
        console.log('Recognition start error:', error);
        updateVoiceStatus('❌ Failed to start');

        // Retry after delay
        setTimeout(() => {
            if (!isListening && !currentAudio) {
                startListening();
            }
        }, 2000);
    }
}

// Start AI Session
function startAISession() {
    const title = document.getElementById('sessionTitle').value.trim();
    const description = document.getElementById('sessionDescription').value.trim();

    if (!title || !description) {
        alert('Please provide both title and description for the session.');
        return;
    }

    // Hide setup, show session
    document.getElementById('sessionSetup').style.display = 'none';
    document.getElementById('sessionActive').style.display = 'block';

    // Initialize components
    connectWebSocket();
    initSpeechRecognition();
    setupCamera();

    // Auto-start voice recognition after WebSocket connects
    if (ws) {
        ws.onopen = function () {
            ws.send(JSON.stringify({
                type: 'start_session',
                title: title,
                description: description
            }));

            // Initiate WebRTC
            initWebRTC();
        };
    }

    // Auto-start listening only
    setTimeout(() => {
        addMessage('System', '🎤 Session started!', 'ai');

        setTimeout(() => {
            startListening();
        }, 2000);
    }, 1000);
}

// Stop voice recognition
function stopVoiceRecognition() {
    if (recognition) {
        try {
            recognition.abort();
            recognition.stop();
            recognition = null;
        } catch (e) {
            console.log('Recognition stop error:', e);
        }
        isListening = false;
        updateVoiceStatus('🔇 Voice Stopped');
    }
}

// End session
function endSession() {
    console.log('Ending session...');
    addMessage('System', '🔄 Ending session...', 'ai');

    // Force stop voice recognition
    stopVoiceRecognition();

    // Stop speech synthesis
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }

    // Close WebSocket
    if (ws) {
        ws.close();
        ws = null;
    }

    // Force stop all media tracks
    if (localStream) {
        console.log('Stopping media tracks...');
        localStream.getTracks().forEach(track => {
            track.stop();
            track.enabled = false;
            console.log(`Force stopped ${track.kind} track, state:`, track.readyState);
        });
        localStream = null;
    }

    // Additional cleanup - stop any remaining media
    navigator.mediaDevices.getUserMedia({ audio: false, video: false }).catch(() => { });

    // Clear video elements
    const userPipView = document.getElementById('userPipView');
    const userMainView = document.getElementById('userMainView');
    if (userPipView) {
        userPipView.srcObject = null;
        userPipView.load();
    }
    if (userMainView) {
        userMainView.srcObject = null;
        userMainView.load();
    }

    // Reset UI
    setTimeout(() => {
        document.getElementById('sessionSetup').style.display = 'block';
        document.getElementById('sessionActive').style.display = 'none';
        document.getElementById('chatContainer').innerHTML = '';
        document.getElementById('sessionTitle').value = '';
        document.getElementById('sessionDescription').value = '';

        // Reset view state
        isAIMainView = true;

        // Reset video views
        const aiMainView = document.getElementById('aiMainView');
        const userMainView = document.getElementById('userMainView');
        const aiPipView = document.getElementById('aiPipView');
        const userPipView = document.getElementById('userPipView');
        const mainLabel = document.getElementById('mainLabel');

        if (aiMainView) {
            aiMainView.style.display = 'flex';
            userMainView.style.display = 'none';
            aiPipView.style.display = 'none';
            userPipView.style.display = 'block';
            mainLabel.textContent = 'AI Assistant';
        }

        updateVoiceStatus('🔇 Session Ended');
        console.log('Session cleanup complete');
    }, 500);
}

// Chat functionality
function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (message && ws) {
        addMessage('You', message, 'user');
        ws.send(JSON.stringify({
            type: 'user_message',
            content: message
        }));
        input.value = '';
    }
}

function addMessage(sender, content, className) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    messageDiv.innerHTML = `<strong>${sender}:</strong> ${content}`;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Setup camera
async function setupCamera() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 720 },
            audio: true
        });

        // Set video to PIP view initially (AI is main)
        document.getElementById('userPipView').srcObject = localStream;

        console.log('Camera setup complete, stream tracks:', localStream.getTracks().length);

    } catch (error) {
        console.error('Error accessing camera:', error);
        addMessage('System', 'Camera access denied. Voice chat will still work.', 'ai');
    }
}

async function initWebRTC() {
    try {
        console.log("Initializing WebRTC...");
        const configuration = {
            iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
        };
        peerConnection = new RTCPeerConnection(configuration);

        // Add local tracks to connection
        if (localStream) {
            localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });
        }

        // Handle ICE candidates
        peerConnection.onicecandidate = function (event) {
            if (event.candidate) {
                // In a real app, send candidate to server
                // ws.send(JSON.stringify({type: 'ice_candidate', candidate: event.candidate}));
            }
        };

        // Create Offer
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        // Send offer to server
        if (ws) {
            ws.send(JSON.stringify({
                type: 'webrtc_offer',
                sdp: offer.sdp
            }));
        }

    } catch (e) {
        console.error("WebRTC Init Error:", e);
    }
}

async function handleWebRTCAnswer(sdp) {
    if (peerConnection) {
        try {
            await peerConnection.setRemoteDescription(new RTCSessionDescription({
                type: 'answer',
                sdp: sdp
            }));
            console.log("WebRTC Answer processed");
        } catch (e) {
            console.error("Error setting remote description:", e);
        }
    }
}

// Enter key support
document.getElementById('messageInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initialize
window.onload = function () {
    // Show setup form on load
};

// Handle page refresh/close - cleanup media
window.addEventListener('beforeunload', function (e) {
    if (localStream) {
        localStream.getTracks().forEach(track => {
            track.stop();
            console.log(`Cleanup: stopped ${track.kind} track`);
        });
    }
    if (recognition) {
        recognition.abort();
    }
    if (ws) {
        ws.close();
    }
});