$(function() {
    // jQuery.material.init(); 
    var activeCountryTabHash,
        urlHash;
    
    
    function sendForm() {
        $('#send-form .show-form').on('click', function() {$('#send-form').addClass("open");});
        $('#send-form .btn-close').on('click', function() {$('#send-form').removeClass("open");});
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

    $('.tooltip-anchor, [data-toggle="tooltip"]').tooltip();
    
    $('.pep-tab .nav-tabs a').click(function (e) {
        e.preventDefault();
        $(this).tab('show');
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
            form.html(data);
        });
    });

    $(".combobox").combobox();

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
