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

    $('.tab__label').on('click', function (e) {
        e.preventDefault();
        const tab = $(this).attr("href");
        console.log(tab);
        $('.tabs__item').each(function () {
            $(this).removeClass('active');
        })
        $(tab).addClass('active');
    })

    $('.alert').on('click', function () {
        $(this).remove();
    })
});