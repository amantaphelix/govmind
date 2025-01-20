document.addEventListener("DOMContentLoaded", function () {
   
    const form = document.getElementById("loginForm");

    form.addEventListener("submit", function (event) {
        const username = form.username.value.trim();
        const password = form.password.value.trim();

        if (!username || !password) {
            alert("Please fill in both the username and password fields.");
            event.preventDefault(); // Prevent form submission
        }
    });

    
    const inputs = document.querySelectorAll("input[type='text'], input[type='password']");

    inputs.forEach(input => {
        input.addEventListener("focus", function () {
            this.style.backgroundColor = "#f0f8ff"; // Light blue color
        });

        input.addEventListener("blur", function () {
            this.style.backgroundColor = ""; // Reset to original background
        });
    });

   
    const signUpLink = document.getElementById("signUpLink");

    if (signUpLink) {
        signUpLink.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent the default link action

            // Smoothly scroll to the section with ID 'signUpSection'
            const signUpSection = document.getElementById("signUpSection");
            if (signUpSection) {
                signUpSection.scrollIntoView({ behavior: "smooth" });
            }
        });
    }
});
