(function () {
    'use strict';

    // ---------- the rules (the message is shown next to the field) ----------

    var rules = {
        fullname: function (value) {
            value = value.trim();
            if (!value) { return 'Full name is required.'; }
            if (!/^\p{L}+(?:[ '\-]+\p{L}+)*$/u.test(value)) {
                return 'Full name can only contain letters, spaces, hyphens, and apostrophes.';
            }
            if (value.length < 2) { return 'Full name must contain at least 2 characters.'; }
            return '';
        },
        username: function (value) {
            value = value.trim();
            if (!value) { return 'Username is required.'; }
            if (!/^[A-Za-z0-9_]+$/.test(value)) {
                return 'Username can only contain letters, numbers, and underscores.';
            }
            if (value.length < 4 || value.length > 20) { return 'Username must be 4 to 20 characters long.'; }
            return '';
        },
        email: function (value) {
            value = value.trim();
            if (!value) { return 'Email address is required.'; }
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) { return 'Please enter a valid email address.'; }
            return '';
        },
        contact: function (value) {
            value = value.trim();
            if (!value) { return 'Contact number is required.'; }
            if (!/^09[0-9]{9}$/.test(value)) { return 'Please enter a valid 11-digit Philippine mobile number.'; }
            if (/([0-9])\1{3}/.test(value)) {
                return 'Contact number cannot have the same digit repeated 4 or more times in a row.';
            }
            return '';
        },
        purok: function (value) {
            if (!value) { return 'Please select your purok / area.'; }
            return '';
        },
        password: function (value) {
            if (!value) { return 'Password is required.'; }
            if (value.length < 8) { return 'Password must contain at least 8 characters.'; }
            if (!(/[A-Z]/.test(value) && /[a-z]/.test(value) && /[0-9]/.test(value) && /[^A-Za-z0-9]/.test(value))) {
                return 'Password must include uppercase, lowercase, number, and special character.';
            }
            return '';
        },
        confirm: function (value, form) {
            var password = form.querySelector('[data-rule="password"]');
            if (!value) { return 'Please confirm your password.'; }
            if (password && value !== password.value) { return 'Passwords do not match.'; }
            return '';
        },
        access: function (value) {
            if (!value.trim()) { return 'Admin access code is required.'; }
            return '';
        },
        login: function (value) {
            value = value.trim();
            if (!value) { return 'Username or email is required.'; }
            if (value.indexOf('@') !== -1) { return rules.email(value); }
            return rules.username(value);
        },
        loginpassword: function (value) {
            if (!value) { return 'Password is required.'; }
            return '';
        }
    };
    window.CommunityBoardRules = rules;

    // ---------- helpers ----------

    function check(input, form) {
        var rule = rules[input.getAttribute('data-rule')];
        var message = rule ? rule(input.value, form) : '';
        var feedback = input.parentElement.querySelector('.invalid-feedback');

        input.setCustomValidity(message);
        input.classList.toggle('is-invalid', message !== '');
        input.classList.toggle('is-valid', message === '' && input.value !== '');
        if (feedback) { feedback.textContent = message; }
        return message === '';
    }

    function showLoading(form) {
        var button = form.querySelector('button[type="submit"]');
        if (!button) { return; }
        button.setAttribute('data-original-html', button.innerHTML);
        // wait one tick so the form is still sent normally
        setTimeout(function () {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' +
                (button.getAttribute('data-loading') || 'Please wait...');
        }, 0);
    }

    // ---------- show / hide password buttons ----------

    document.querySelectorAll('.toggle-password').forEach(function (button) {
        button.addEventListener('click', function () {
            var input = button.parentElement.querySelector('input');
            var icon = button.querySelector('i');
            var showing = input.type === 'text';
            var willShow = !showing;
            input.type = showing ? 'password' : 'text';
            icon.className = willShow ? 'bi bi-eye-slash' : 'bi bi-eye';
            button.setAttribute('aria-label', willShow ? 'Hide password' : 'Show password');
        });
    });

    // ---------- every form with the needs-validation class ----------

    document.querySelectorAll('.needs-validation').forEach(function (form) {
        var ruleFields = form.querySelectorAll('[data-rule]');

        ruleFields.forEach(function (input) {
            input.addEventListener('blur', function () { check(input, form); });

            input.addEventListener('input', function () {
                if (input.getAttribute('data-rule') === 'contact') {
                    var digits = input.value.replace(/[^0-9]/g, '');  // numbers only
                    if (digits.length >= 1 && digits[0] !== '0') { digits = ''; }  // must start with 0
                    if (digits.length >= 2 && digits[1] !== '9') { digits = digits.slice(0, 1); }  // then 9
                    input.value = digits;
                }
                var alreadyChecked = input.classList.contains('is-invalid') || input.classList.contains('is-valid');
                if (alreadyChecked) { check(input, form); }

                if (input.getAttribute('data-rule') === 'password') {
                    var confirm = form.querySelector('[data-rule="confirm"]');
                    if (confirm && confirm.value !== '') { check(confirm, form); }
                }
            });
        });

        form.addEventListener('submit', function (event) {
            if (event.defaultPrevented) { return; }  // for example, the user pressed Cancel on a confirm box

            var firstBad = null;
            ruleFields.forEach(function (input) {
                if (!check(input, form) && !firstBad) { firstBad = input; }
            });

            // other forms (reset / change password) still use the simple match check
            var password = form.querySelector('#password');
            var confirmBox = form.querySelector('#confirm_password');
            if (password && confirmBox && !confirmBox.hasAttribute('data-rule')) {
                confirmBox.setCustomValidity(password.value !== confirmBox.value ? 'Passwords do not match' : '');
            }

            var summary = form.querySelector('.form-summary');
            if (firstBad || !form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                if (summary) { summary.classList.remove('d-none'); }
                if (firstBad) { firstBad.focus(); }
                form.classList.add('was-validated');
                return;
            }

            if (summary) { summary.classList.add('d-none'); }
            showLoading(form);
        });
    });

    // coming back with the Back button: bring the buttons back to normal
    window.addEventListener('pageshow', function () {
        document.querySelectorAll('button[data-original-html]').forEach(function (button) {
            button.disabled = false;
            button.innerHTML = button.getAttribute('data-original-html');
            button.removeAttribute('data-original-html');
        });
    });
})();
