$( document ).ready(function() {
    $('#form-register').on('submit', function (e) {
        e.preventDefault();
        const constraints = { from: { email: true } };
        const email = e.currentTarget[0].value;

        if (!validate({from: email}, constraints)) {
            $('#form-register-email').removeClass('error').addClass('valid')
            e.currentTarget.submit();
        } else {
            $('#form-register-email').removeClass('valid').addClass('error')
        }
    })

    $('.form__alert').on('click', function () {
        $(this).remove();
    })
});