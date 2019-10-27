$(function() {
    // jQuery.material.init(); 
    var activeCountryTabHash,
        urlHash;
    
    function square_height() {
        $(".square").each(function() {
            var cw = $(this).width();
            $(this).css({
                'height': cw + 'px'
            });
        });
    }
    
    function sendForm() {
        $('#send-form .show-form').on('click', function() {$('#send-form').addClass("open");});
        $('#send-form .btn-close').on('click', function() {$('#send-form').removeClass("open");});
    }
    
    equalheight = function(container){
        var currentTallest = 0,
             currentRowStart = 0,
             rowDivs = new Array(),
             $el,
             topPosition = 0;
         $(container).each(function() {
        
           $el = $(this);
           $($el).height('auto')
           topPostion = $el.position().top;
        
           if (currentRowStart != topPostion) {
             for (currentDiv = 0 ; currentDiv < rowDivs.length ; currentDiv++) {
               rowDivs[currentDiv].height(currentTallest);
             }
             rowDivs.length = 0; // empty the array
             currentRowStart = topPostion;
             currentTallest = $el.height();
             rowDivs.push($el);
           } else {
             rowDivs.push($el);
             currentTallest = (currentTallest < $el.height()) ? ($el.height()) : (currentTallest);
          }
           for (currentDiv = 0 ; currentDiv < rowDivs.length ; currentDiv++) {
             rowDivs[currentDiv].height(currentTallest);
           }
         });
    }
    
    function setCountryPaginationHash() {
        activeCountryTabHash = $('.pep-tab .nav-tabs li.active a').attr('href');
        $('#pepTabContent .tab-pane.active .pagination a').each(function() {
            href = $(this).attr('href');
            pos = href.indexOf('#');
            if (pos < 0) {
                $(this).attr('href', href  + activeCountryTabHash);
            } else {
                originalUrl = href.substr(0, pos);
                $(this).attr('href', originalUrl  + activeCountryTabHash);
            }
        });
    }
    
    function setFixedWidth(selector, container) {
        $(selector).css('width', $(container).width());
    }

    equalheight(".small-profile");

    $('.tooltip-anchor, [data-toggle="tooltip"]').tooltip();
    
    $('.pep-tab .nav-tabs a').click(function (e) {
        e.preventDefault();
        $(this).tab('show');
    });
    
    $('.pep-tab a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        equalheight(".small-profile");
        setCountryPaginationHash();
    });
    
    $(".as-select .dropdown-menu li a").click(function(){
        $(this).parents(".as-select").find(".dropdown-toggle").html($(this).html() + " <span class=\"caret\"></span>");
    });
    
    sendForm();
    
    $(document).ready(function() {  
        $(".nice-scroll").niceScroll({cursorcolor:"#355383"});
        
        urlHash = window.location.hash;
        $('.pep-tab .nav-tabs a[href="' + urlHash + '"]').tab('show');
        setCountryPaginationHash();
    });

    $(window).resize(function() {
        square_height();
        equalheight(".small-profile");
        setFixedWidth('#side-profilemenu.affix', '#profile-nav');
    });
    
    $('#side-profilemenu').on('affixed.bs.affix', function () {
        setFixedWidth('#side-profilemenu.affix', '#profile-nav');
    });
    
    $('#side-profilemenu').on('affixed-top.bs.affix', function () {
        $('#side-profilemenu').css('width', '100%');
    });

    $("#search-form").typeahead({
        minLength: 2,
        items: 100,
        autoSelect: false,
        source: function(query, process) {
            $.get($("#search-form").data("endpoint"), {
                    "q": query
                })
                .done(function(data) {
                    process(data);
                })
        },
        matcher: function() {
            // Big guys are playing here
            return true;
        },
        afterSelect: function(item) {
            var form = $("#search-form").closest("form");
            form.find("input[name=is_exact]").val("on");

            form.submit();
        }
    });

    $("#search-form-body").typeahead({
        minLength: 2,
        items: 100,
        autoSelect: false,
        source: function(query, process) {
            $.get($("#search-form-body").data("endpoint"), {
                    "q": query
                })
                .done(function(data) {
                    process(data);
                })
        },
        matcher: function() {
            // Big guys are playing here
            return true;
        },
        afterSelect: function(item) {
            var form = $("#search-form-body").closest("form");
            form.find("input[name=is_exact]").val("on");

            form.submit();
        }
    });

    $('.tree > ul > li > ul > li:has(ul)')
        .addClass('parent_li')
        .find(' > span')
        .attr('title', 'Collapse this branch');

    $('.tree li.parent_li > span').on('click', function(e) {
        var children = $(this).parent('li.parent_li').find(' > ul > li'),
            speed;

        if (children.length > 100) {
            speed = null;
        }
        else {
            speed = "fast";
        }
        
        if (children.is(":visible")) {
            children.hide(speed);
            $(this)
                .attr('title', 'Expand this branch')
                .find(' > i.faicon')
                .addClass('fa-plus-square')
                .removeClass('fa-minus-square');
        } else {
            children.show(speed);
            $(this)
                .attr('title', 'Collapse this branch')
                .find(' > i.faicon')
                .addClass('fa-minus-square')
                .removeClass('fa-plus-square');
        }
        e.stopPropagation();
    });

    $('#side-profilemenu').affix({
        offset: {
            top: 50
        }
    });

    $("body").on("click", ".active-box", function(e) {
        var el = $(this);
        location.href = el.data("url");
    });

    $("body").on("click", ".print-me", function(e) {
        e.preventDefault();
        window.print();
    });
    
    $("body").on("click", ".trigger-hidden-row", function(e) {
        var $this = $(this),
            $row = $this.parents("tr").next(".additional_hidden");
            
       $this.toggleClass("fa-plus-square fa-minus-square");
       $row.toggleClass("hidden");
    });

    $("body").on("submit", ".ajax-form", function(e) {
        e.preventDefault();
        var form = $(this).closest("form");
        form.find("button").attr("disabled", "disabled");

        $.post(form.attr("action"), form.serialize(), function(data) {
            form.parent().html(data);
        });
    });

    $(".combobox").combobox();

    $(".country-list").change(function(e) {
        var s = $(this).find(":selected").data("url");

        if (typeof(s) !== "undefined") {
            window.location = s;
        }
    });

    function track_element(el, action) {
        var el = $(el);

        var eventCategory = el.data('ga-event-category'),
            eventAction = el.data('ga-event-action'),
            eventLabel = el.data('ga-event-label');

        if (action) {
            eventAction += "-" + action
        }

        if (typeof(ga) !== "undefined") {
            ga('send', 'event', eventCategory, eventAction, eventLabel);
        }
    }

    $(".track-ga-event").each(function() {track_element(this, "")});
    $(".track-ga-event-click").on("click", function() {track_element(this, "click")});
});
