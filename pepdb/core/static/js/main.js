$(document).ready(function () {

    // burger open
    $('.burger-btn').on('click', function (e) {
        e.preventDefault();
        if ($(this).hasClass('burger-btn--active')) {

            $(this).removeClass('burger-btn--active');

            $('body').removeClass('menu-open');

        } else {
            $(this).addClass('burger-btn--active');

            $('body').addClass('menu-open');
        }

    });

    // check window size
    $(window).resize(function () {
        // for burger
        if ($(window).width() >= 1024) {
            $('body').removeClass('menu-open');
            $('.burger-btn').removeClass('burger-btn--active');
        }

        // for main partners-slider
        if ($(window).width() <= 767) {
            $('.partners .items').slick({
                    slidesToShow: 1,
                    slidesToScroll: 1,
                    dots: true,
                    arrows: false,
                    infinite: false
                }
            );
        } else {
            $('.partners .items').slick('unslick');
        }

        // for main opportunities-slider
        if ($(window).width() <= 767) {
            $('.opportunities .items').slick({
                    slidesToShow: 1,
                    slidesToScroll: 1,
                    dots: true,
                    arrows: false,
                    infinite: false,
                    adaptiveHeight: true
                }
            );
        } else {
            $('.opportunities .items').slick('unslick');
        }

        //create trigger to resizeEnd event
        if (this.resizeTO) clearTimeout(this.resizeTO);
        this.resizeTO = setTimeout(function () {
            $(this).trigger('resizeEnd');
        }, 500);
    });

    //resize chart after window resize end
    $(window).on('resizeEnd', function () {
        drawChart();
    });

    // open/close header search
    $('.header .search-btn').on('click', function (e) {
        e.preventDefault();
        $('.menu').toggleClass('slide-out-top');
        $('.form-wrap').toggleClass('form-wrap--open');
    });

    // first section bg
    if ($('div').is('#particles-js')) {
        particlesJS.load('particles-js', 'js/particlesjs-config.json', function () {
        });
    }

    //open/close search dropdown
    $('.search-form input').focusin(function () {
        $(this).parents('.search-form').addClass('search-form--open-dropdown');
    }).focusout(function () {
        $(this).parents('.search-form').removeClass('search-form--open-dropdown');
    })

    // main section blog scroll
    // $('.blog-and-investigation .items').perfectScrollbar({
    //     maxScrollbarLength: 60,
    // });

    if ($("section").is(".blog-and-investigation")) {
        new SimpleBar($('.blog-and-investigation .items')[0]);
    }
    // new SimpleBar($('.blog-and-investigation .items')[0]);

    // main partners-slider
    if ($(window).width() <= 767) {
        $('.partners .items').slick({
            slidesToShow: 1,
            slidesToScroll: 1,
            dots: true,
            arrows: false,
            infinite: false
        });
    }

    // main opportunities-slider section
    if ($(window).width() <= 767) {
        $('.opportunities .items').slick({
            slidesToShow: 1,
            slidesToScroll: 1,
            dots: true,
            arrows: false,
            infinite: false,
            adaptiveHeight: true
        });
    }

    // profiles filters
    $('.profiles-filters a').on('click', function (e) {
        e.preventDefault();
        if ($(this).attr('id') == 'individuals-filter') {
            $(this).addClass('active');
            $('#entities-filter').removeClass('active');
            $('#entities-items').removeClass('active');
            $('#individuals-items').addClass('active');
        } else if ($(this).attr('id') == 'entities-filter') {
            $(this).addClass('active');
            $('#individuals-filter').removeClass('active');
            $('#individuals-items').removeClass('active');
            $('#entities-items').addClass('active');
        }
    });

    //footer founders open/close
    $('.footer__founders .title').on('click', function () {
        if ($(window).width() <= 767) {
            $(this).toggleClass('title--open');
            $('.footer__founders .text').toggleClass('text--show');
            $('.footer__bottom .description').toggleClass('description--show');
        }
    });

    // close modal
    $('.modal-close').on('click', function (e) {
        e.preventDefault();
        $('.modal').removeClass('modal--open');
        $('body').removeClass('modal-open');
    });
    $(document).mouseup(function (e) {
        var container = $(".modal-inner");
        if (!container.is(e.target) && container.has(e.target).length === 0) {
            container.parents('.modal').removeClass('modal--open');
            $('body').removeClass('modal-open');
        }
    });

    // found-modal open
    $('#found').on('click', function (e) {
        e.preventDefault();
        $('#found-modal').addClass('modal--open');
        $('body').addClass('modal-open');
    });

    // tell-info-modal open
    $('#tell-info').on('click', function (e) {
        e.preventDefault();
        $('#tell-info-modal').addClass('modal--open');
        $('body').addClass('modal-open');
    });

    // analytics-modal open
    $('#analytics').on('click', function (e) {
        e.preventDefault();
        $('#analytics-modal').addClass('modal--open');
        $('body').addClass('modal-open');
    });

    // faq item open-close
    $('.faq-item__header').on('click', function () {
        $(this).parents('.faq-item').toggleClass('faq-item--open');
    });

    //open side-menu
    $('.side-menu-btn a').on('click', function (e) {
        e.preventDefault();
        $('.side-menu').addClass('side-menu--open');
        $('body').addClass('no-scroll');
    });

    //close side-menu
    $('.side-menu-close').on('click', function (e) {
        e.preventDefault();
        $('.side-menu').removeClass('side-menu--open');
        $('body').removeClass('no-scroll');
    });

    // scroll to section
    $(".side-menu .links-wrap a").on("click", function (event) {
        event.preventDefault();
        var id = $(this).attr('href');
        var top = $(id).offset().top;
        $('body,html').animate({scrollTop: top}, 1500);
        $('.side-menu').removeClass('side-menu--open');
        $('body').removeClass('no-scroll');
    });

    //side menu scrollbar
    if ($("div").is(".side-menu__container")) {
        new SimpleBar($('.side-menu__container')[0]);
    }


    // scoring open/close
    $('.scoring__btn').on('click', function (e) {
        e.preventDefault();
        $('.scoring').toggleClass('scoring--open');
    });

    // scoring index
    $(function () {
        $('.progressbar .index').height($('.progressbar').width() / 10);

        $(window).resize(function () {
            $('.progressbar .index').height($('.progressbar').width() / 10);
        });
    });

    // toggle-table-row
    $('.toggle-row-btn').on('click', function () {
        var parentRow = $(this).parents('tr');
        parentRow.next('.toggle-row').toggleClass('toggle-row--open');
        $(this).toggleClass('toggle-row-btn--open');
    });

    // check profile-section content height
    var profileSectionBody = $('.profile-section__body');
    profileSectionBody.each(function (i, elem) {
        var childrenHeight = $(this).children().height();
        if (childrenHeight > 300) {
            $(this).addClass('profile-section__body--hidden');
            // init scrollbar
            new SimpleBar($(this)[0]);
            $(this).siblings('.profile-section__footer').children('.more-btn').addClass('show');
        }
    });

    // show-all in profile section
    $('.more-btn').on('click', function () {
        $(this).parents('.profile-section').children('.profile-section__body').toggleClass('profile-section__body--show-all');
        $(this).toggleClass('show-less');
    });

    // toggle table/chart
    $('.show-graph').on('click', function () {
        $(this).addClass('active');
        $(this).siblings('.show-table').removeClass('active');
        $(this).parents('.profile-section').children('.profile-section__body').addClass('profile-section__body--show-chart');
        $(this).parents('.profile-section').children('.profile-section__footer').addClass('profile-section__footer--hide-btn');
        drawChart();
    });

    $('.show-table').on('click', function () {
        $(this).addClass('active');
        $(this).siblings('.show-graph').removeClass('active');
        $(this).parents('.profile-section').children('.profile-section__body').removeClass('profile-section__body--show-chart');
        $(this).parents('.profile-section').children('.profile-section__footer').removeClass('profile-section__footer--hide-btn');
    });

    // close pie-chart popup

    $('.chart-popup__close').on('click', function () {
        $(this).parents('.chart-popup').removeClass('show');
    })

    // open dossier modal
    $('#show-dossier').on('click', function () {
        $('#dossier-modal').addClass('modal--open');
        $('body').addClass('modal-open');
    })

    // open criminal modal
    $('#show-criminal-story').on('click', function () {
        $('#criminal-modal').addClass('modal--open');
        $('body').addClass('modal-open');
    })

});
