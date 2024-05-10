window.onload = function() {
    var matrixContainer = document.querySelector('.matrix');
    var colors = ['#0f0', '#0b0', '#060', '#030']; 

    for (var i = 0; i < 100; i++) {
        var span = document.createElement('span');
        span.textContent = generateBinarySequence(7);
        span.style.color = colors[Math.floor(Math.random() * colors.length)];
        span.style.left = Math.random() * window.innerWidth + 'px';
        span.style.animationDuration = 8 + Math.random() * 10 + 's'; 
        matrixContainer.appendChild(span);
    }
};

function generateBinarySequence(length) {
    return Array.from({length: length}, () => Math.floor(Math.random() * 2)).join('');
}
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-messages li');
    flashMessages.forEach(function(msg) {
        setTimeout(function() {
            let opacity = 1;
            const timer = setInterval(function() {
                if (opacity <= 0.1) {
                    clearInterval(timer);
                    msg.style.display = 'none';
                }
                msg.style.opacity = opacity;
                msg.style.filter = 'alpha(opacity=' + opacity * 100 + ")";
                opacity -= opacity * 0.1;
            }, 50);
        }, 5000); // Hides after 5 seconds
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const typingInstructions = "Please Enter the credentials to login.";
    let i = 0;
    const speed = 50; // typing speed in milliseconds

    function typeWriter() {
        if (i < typingInstructions.length) {
            document.getElementById("typing-instructions").textContent += typingInstructions.charAt(i);
            i++;
            setTimeout(typeWriter, speed);
        }
    }

    typeWriter();
});
