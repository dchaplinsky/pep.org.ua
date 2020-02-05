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
        if ($("section").is(".partners")) {
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
                $('.partners .items').filter('.slick-initialized').slick('unslick');
            }
        }

        // for main opportunities-slider
        if ($("section").is(".opportunities")) {
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
                $('.opportunities .items').filter('.slick-initialized').slick('unslick');
            }
        }

        // create trigger to resizeEnd event
        if (this.resizeTO) clearTimeout(this.resizeTO);
        this.resizeTO = setTimeout(function () {
            $(this).trigger('resizeEnd');
        }, 500);

        //  for fixed side btn
        if ($('div').is('.profile-page')) {
            fixedSideMenu();
        }

        // fixed main-page side link
        if ($('div').is('.main-page')) {
            fixedMainPageLink();
        }
    });

    //resize chart after window resize end
    $(window).on('resizeEnd', function () {
        if ($('div').hasClass('profile-page')) {
            drawChart();
        }
    });

    // open/close header search
    $('.header .search-btn').on('click', function (e) {
        e.preventDefault();
        $('.menu').toggleClass('slide-out-top');
        $('.form-wrap').toggleClass('form-wrap--open');
    });

    // first section bg
    if ($('div').is('#particles-js')) {
        particlesJS.load('particles-js', $(location).attr('origin') + '/static/js/particlesjs-config.json', function () {
        });
    }

    //open/close search dropdown
    $('.search-form input').focusin(function () {
        $(this).parents('.search-form').addClass('search-form--open-dropdown');
    }).focusout(function () {
        $(this).parents('.search-form').removeClass('search-form--open-dropdown');
    })

    // main section blog scroll
    if ($("section").is(".blog-and-investigation")) {
        new SimpleBar($('.blog-and-investigation .items')[0]);
    }

    // main partners-slider
    if ($(window).width() <= 767) {
        if ($("section").is(".partners")) {
            $('.partners .items').slick({
                slidesToShow: 1,
                slidesToScroll: 1,
                dots: true,
                arrows: false,
                infinite: false
            });
        }
    }

    // main opportunities-slider section
    if ($(window).width() <= 767) {
        if ($("section").is(".opportunities")) {
            $('.opportunities .items').slick({
                slidesToShow: 1,
                slidesToScroll: 1,
                dots: true,
                arrows: false,
                infinite: false,
                adaptiveHeight: true
            });
        }
    }

    // profiles filters
    $('.profiles-filters button').on('click touchstart', function (e) {
        e.preventDefault();
        if ($(this).attr('id') == 'individuals-filter') {
            $(this).addClass('active');
            $('#entities-filter').removeClass('active');
            $('#entities-items').removeClass('active');
            $('.pagination.entities').removeClass('active');
            $('#individuals-items').addClass('active');
            $('.pagination.individuals').addClass('active');

        } else if ($(this).attr('id') == 'entities-filter') {
            $(this).addClass('active');
            $('#individuals-filter').removeClass('active');
            $('#individuals-items').removeClass('active');
            $('.pagination.individuals').removeClass('active');
            $('#entities-items').addClass('active');
            $('.pagination.entities').addClass('active');
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

    function hideModal(e) {
        if (e.keyCode === 27) {
            $('.modal').removeClass('modal--open');
            $('body').removeClass('modal-open');
        }
    }

    $(document).keyup(hideModal);
    // $(document).mouseup(function (e) {
    //     var container = $(".modal-inner");
    //     if (!container.is(e.target) && container.has(e.target).length === 0) {
    //         container.parents('.modal').removeClass('modal--open');
    //         $('body').removeClass('modal-open');
    //     }
    // });

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
        $('body,html').animate({ scrollTop: top }, 1500);
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
    });

    // open dossier modal
    $('#show-dossier').on('click', function () {
        $('#dossier-modal').addClass('modal--open');
        $('body').addClass('modal-open');
    });

    // open criminal modal
    $('#show-criminal-story').on('click', function () {
        $('#criminal-modal').addClass('modal--open');
        $('body').addClass('modal-open');
    });

    // open visualization modal
    $('.visualization-btn').on('click', function () {
        $('#visualization-modal').addClass('modal--open');
        $('body').addClass('modal-open');
        $(function modalBodyHeight() {
            var modal = $('#visualization-modal'),
                modalHeight = modal.find('.visualization-modal').height(),
                headerHeight = modal.find('.visualization-modal__header').outerHeight(),
                bodyHeight = modalHeight - headerHeight;
            modal.find('.visualization-modal__body').css("height", bodyHeight + "px");
        })
    });

    //show/hide legend
    $('.legend-btn').on('click', function () {
        $('.legend-wrap').toggleClass('legend-wrap--open');
    });

    //visualization modal body height


    // сортировка таблицы
    $(".sort-table tr th").click(function (event) {

        // если текущий столбец не сортируемый - ничего не делаем
        if ($(this).attr("data-colnum") == undefined) return false;

        // текущая таблица (3 шт parent, т.к. боаузер дорисовывает tbody и thead)
        var currTable = $(this).parent().parent().parent();

        // удаляем ряд с доп инфо
        currTable.find('.toggle-row').remove();

        // сносим флаг открытого доп инфо
        currTable.find(".toggle-row-btn").removeClass("open");

        // количество игнорируемых сортировкой строк (шапка таблицы)
        var sliceCnt = currTable.data("slice-count");

        // получаем идентификатор сортируемого столбца
        var sortColNum = $(this).data("colnum");
        var from, to;

        // определяем в какую сторону сортировать
        if (!$(this).hasClass("asc") && !$(this).hasClass("desc")) {
            $(this).addClass("asc");
            from = 1;
            to = -1;

        } else if ($(this).hasClass("asc")) {
            $(this).removeClass("asc").addClass("desc");
            from = -1;
            to = 1;

        } else if ($(this).hasClass("desc")) {
            $(this).removeClass("desc").addClass("asc");
            from = 1;
            to = -1;
        }

        // удаляем старые классы указывающие текущее направление сортировки
        $(this).siblings("th").removeClass("asc desc");

        // сортируем
        currTable.find('tr').slice(sliceCnt).sort(function (a, b) {
            if ($(a).find('.sort-col.' + sortColNum).text().localeCompare($(b).find('.sort-col.' + sortColNum).text()) > 0) {
                return from;
            } else {
                return to;
            }
            // return $(a).find('.sort-col.' + sortColNum).text() > $(b).find('.sort-col.' + sortColNum).text() ? from : to;
        }).appendTo(currTable);
    });

    // скрытие/отображение доп инфо
    $(".toggle-row-btn").click(function (event) {
        var infoRow = $(this).parent().parent();
        console.log(infoRow);

        // если для текущего ряда доп инфо уже отображается - скрываем (по факту удаляем)
        if ($(this).hasClass("open")) {
            // удаляем ряд с доп инфо
            infoRow.next(".toggle-row").remove();
            $(this).removeClass("open");

            // если доп инфо еще не было отображено - показываем
        } else {
            // удаляем другие ряды с доп инфо, если были открыты
            // infoRow.siblings(".toggle-row").remove();

            // копируем лежащий рядом с кнопкой блок контента с доп инфо (который имеет класс .toggle-content)
            var content = $(this).siblings(".toggle-content")[0].outerHTML;

            // формируем ряд с доп инфо и вставляем его после родительского ряда
            $(this).parent().parent().after('<tr class="toggle-row"><td colspan="4">' + content + '</td></tr>');

            // отображаем скрытый контент
            infoRow.next(".toggle-row").find(".toggle-content").show();

            // добавляем класс на будущее, чтобы знать, что для текущего ряда инфо блок уже открыт
            $(this).addClass("open");
        }
    });

    // fixed side menu
    function fixedSideMenu() {
        var offsetSideBtn = $('.side-menu-btn').offset();
        var parentHeight = $('.side-menu-btn').parents('.profile-page__content').height();

        $(window).on("scroll", function (e) {
            if ($(window).width() >= 768) {
                if ($(window).scrollTop() >= offsetSideBtn.top - 50
                    && $(window).scrollTop() <= parentHeight - ($('.side-menu-btn').height() + 50)) {
                    $('.side-menu-btn').addClass("side-menu-btn--fixed").removeClass('side-menu-btn--fixed-bottom')
                } else if ($(window).scrollTop() >= parentHeight - ($('.side-menu-btn').height() + 50)) {
                    $('.side-menu-btn').addClass("side-menu-btn--fixed-bottom")
                } else {
                    $('.side-menu-btn').removeClass('side-menu-btn--fixed side-menu-btn--fixed-bottom')
                }
            } else if ($(window).width() <= 767) {
                if ($(window).scrollTop() >= offsetSideBtn.top
                    && $(window).scrollTop() <= parentHeight - ($('.side-menu-btn').height())) {
                    $('.side-menu-btn').addClass("side-menu-btn--fixed").removeClass('side-menu-btn--fixed-bottom')
                } else if ($(window).scrollTop() >= parentHeight - ($('.side-menu-btn').height() + 56)) {
                    $('.side-menu-btn').addClass("side-menu-btn--fixed-bottom")
                } else {
                    $('.side-menu-btn').removeClass('side-menu-btn--fixed side-menu-btn--fixed-bottom')
                }
            }
        });
    }

    if ($('div').is('.profile-page')) {
        fixedSideMenu();
    }

    // fixed main-page side link
    function fixedMainPageLink() {
        var offsetSideLink = $('.zero-corruption-link').offset();
        var parentHeight = $('.zero-corruption-link').parents('main').height();

        $(window).on("scroll", function (e) {
            if ($(window).width() >= 1366) {
                if ($(window).scrollTop() >= (offsetSideLink.top - 80)
                    && $(window).scrollTop() <= parentHeight + $('.first-section').innerHeight() - ($('.zero-corruption-link').height() + 80)) {
                    $('.zero-corruption-link').addClass("zero-corruption-link--fixed").removeClass('zero-corruption-link--fixed-bottom')
                } else if ($(window).scrollTop() >= parentHeight + $('.first-section').innerHeight() - ($('.zero-corruption-link').height() + 80)) {
                    $('.zero-corruption-link').addClass("zero-corruption-link--fixed-bottom")
                } else {
                    $('.zero-corruption-link').removeClass('zero-corruption-link--fixed zero-corruption-link--fixed-bottom')
                }
            } else if ($(window).width() >= 1024) {
                if ($(window).scrollTop() >= (offsetSideLink.top - 70)
                    && $(window).scrollTop() <= parentHeight + $('.first-section').innerHeight() - ($('.zero-corruption-link').height() + 70)) {
                    $('.zero-corruption-link').addClass("zero-corruption-link--fixed").removeClass('zero-corruption-link--fixed-bottom')
                } else if ($(window).scrollTop() >= parentHeight + $('.first-section').innerHeight() - ($('.zero-corruption-link').height() + 70)) {
                    $('.zero-corruption-link').addClass("zero-corruption-link--fixed-bottom")
                } else {
                    $('.zero-corruption-link').removeClass('zero-corruption-link--fixed zero-corruption-link--fixed-bottom')
                }
            } else if ($(window).width() >= 768) {
                if ($(window).scrollTop() >= (offsetSideLink.top - 60)
                    && $(window).scrollTop() <= parentHeight + $('.first-section').innerHeight() - ($('.zero-corruption-link').height() + 60)) {
                    $('.zero-corruption-link').addClass("zero-corruption-link--fixed").removeClass('zero-corruption-link--fixed-bottom')
                } else if ($(window).scrollTop() >= parentHeight + $('.first-section').innerHeight() - ($('.zero-corruption-link').height() + 60)) {
                    $('.zero-corruption-link').addClass("zero-corruption-link--fixed-bottom")
                } else {
                    $('.zero-corruption-link').removeClass('zero-corruption-link--fixed zero-corruption-link--fixed-bottom')
                }
            }
        });
    }

    if ($('div').is('.main-page')) {
        fixedMainPageLink();
    }
});
