$(function() {
    function get_edge_description(obj) {
        var share = obj.data("share");
        if (share > 0) {
            return obj.data("relation") + "\n " + share  + "%";
        } else {
            return obj.data("relation")
        }
        
    }
    var preview_style = [{
        selector: "edge",
        style: {
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            width: 0
        }
    }, {
        selector: "edge[?is_latest]",
        style: {
            width: 1
        }
    }, {
        selector: 'node',
        style: {
            "content": "",
            "font-size": 20,
            "ghost": "yes",
            "text-wrap": "wrap",
            "text-max-width": 100,
            "text-valign": "bottom",
            "text-halign": "center",
            "width": 60,
            "height": 60,
            color: "#FAFAFA"
        }
    }, {
        selector: 'node[model="person"]',
        style: {
            "background-image": "/static/images/cytoscape/person.svg",
            "background-fit": "contain",
            "background-color": "white"
        }
    }, {
        selector: 'node[model="company"]',
        style: {
            "background-image": "/static/images/cytoscape/company.svg",
            "background-fit": "contain",
            "background-color": "white"
        }
    }, {
        selector: 'node.hover',
        style: {
            "text-background-color": "#265eb7",
            "text-background-opacity": 0.8,
            "text-background-shape": "roundrectangle",
            "text-background-padding": "3px",
            "z-index": 100,
            content: "data(name)"
        }
    }, {
        selector: 'node[?is_pep]',
        style: {
            "width": 70,
            "height": 70,
            "background-color": "white",
            "background-image": "/static/images/cytoscape/pep_person.svg"
        }
    }, {
        // (4, _("Пов'язана особа")),
        selector: 'node[type_of_official=4]',
        style: {
            "background-image": "/static/images/cytoscape/affiliated_person.svg"
        }
    }, {
        // (5, _("Член сім'ї")),
        selector: 'node[type_of_official=5]',
        style: {
            "background-image": "/static/images/cytoscape/relative_person.svg"
        }
    }, {
        selector: 'node[?state_company]',
        style: {
            "width": 70,
            "height": 70,
            "background-color": "white",
            "background-image": "/static/images/cytoscape/state_company.svg"
        }
    }, {
        selector: 'node[model="person"][?is_dead]',
        style: {
            "background-image": "/static/images/cytoscape/dead/person.svg",
        }
    }, {
        selector: 'node[model="company"][?is_closed]',
        style: {
            "background-image": "/static/images/cytoscape/dead/company.svg",
        }
    }, {
        selector: 'node[?is_pep][?is_dead]',
        style: {
            "background-image": "/static/images/cytoscape/dead/pep_person.svg"
        }
    }, {
        // (4, _("Пов'язана особа")),
        selector: 'node[type_of_official=4][?is_dead]',
        style: {
            "background-image": "/static/images/cytoscape/dead/affiliated_person.svg"
        }
    }, {
        // (5, _("Член сім'ї")),
        selector: 'node[type_of_official=5][?is_dead]',
        style: {
            "background-image": "/static/images/cytoscape/dead/relative_person.svg"
        }
    }, {
        selector: 'node[?state_company][?is_closed]',
        style: {
            "background-image": "/static/images/cytoscape/dead/state_company.svg"
        }
    }, {
            selector: 'node[?is_main]',
        style: {
            "width": 80,
            "height": 80,
            "text-background-color": "#265eb7",
            "text-background-opacity": 0.8,
            "text-background-shape": "roundrectangle",
            "text-background-padding": "3px",
            content: "data(name)",
            "z-index": 90
        }
    }];
    var full_style = preview_style.concat([{
        selector: 'node',
        style: {
            "content": "data(name)",
            "color": "#666666",
            "min-zoomed-font-size": 18,
            "font-size": 12
        }
    }, {
        selector: 'node[?is_main]',
        style: {
            "width": 80,
            "height": 80,
            "color": "#444444",
            "text-background-color": "white",
            "text-background-opacity": 0,
            content: "data(name)",
            "z-index": 90
        }
    }, {
        selector: "edge",
        style: {
            width: 0
        }
    }, {
        selector: "edge.hover",
        style: {
            label: get_edge_description,
            "text-wrap": "wrap",
            "text-max-width": 100,
            "color": "#666666",
            "font-size": 14,
            "min-zoomed-font-size": 10,
            "text-background-color": "white",
            "z-index": 140,
            "text-background-opacity": 0.8,
            "text-background-shape": "roundrectangle",
        }
    }, {
        selector: "edge.active",
        style: {
            label: get_edge_description,
            "line-color": "red",
            "font-size": 10,
            "text-wrap": "wrap",
            "text-max-width": 80,
            "color": "#666666",
            width: "mapData(share, 0, 100, 0.5, 5)"
        }
    }, {
        selector: "edge[?is_latest]",
        style: {
            width: "mapData(share, 0, 100, 0.5, 5)"
        }
    }, {
        selector: 'edge[model="person2person"]',
        style: {
            "line-style": "dashed"
        }
    }]);

    function init_preview(elements) {
        var cy_preview = cytoscape({
            userPanningEnabled: false,
            autoungrabify: true,
            container: $('#cy-preview'),
            elements: elements,
            layout: {
                name: 'cose',
                quality: 'default'
            },
            style: preview_style
        }).on('mouseover', 'node', function(event) {
            event.target.addClass("hover");
        }).on('mouseout', 'node', function(event) {
            event.target.removeClass("hover");
        });
    }
    var makeTippy = function(node, text, theme, placement) {
        return tippy(node.popperRef(), {
            content: function() {
                var div = document.createElement('div');
                div.innerHTML = text;
                return div;
            },
            trigger: 'manual',
            arrow: false,
            placement: placement,
            hideOnClick: false,
            multiple: true,
            distance: 0,
            interactive: true,
            animateFill: false,
            theme: theme,
            sticky: true
        });
    };

    function init_full(elements) {
        var cy_full = cytoscape({
                container: $('.cy-full'),
                elements: elements,
                style: full_style
            }),
            edge_length = Math.max(50, 3 * elements["nodes"].length),
            partial_layout_options = {
                name: document.location.search.indexOf("euler") != -1 ? 'euler' : "cose",
                animate: "end",
                fit: true,
                padding: 10,
                initialTemp: 100,
                animationDuration: 1500,
                nodeOverlap: 6,
                maxIterations: 3000,
                idealEdgeLength: edge_length,
                nodeDimensionsIncludeLabels: true,
                springLength: edge_length * 3,
                gravity: -15,
                theta: 1,
                stop: function() {
                    cy_full.resize();
                }
            },
            layout_options = {
                name: document.location.search.indexOf("euler") != -1 ? 'euler' : "cose",
                animationDuration: 1500,
                animate: "end",
                springLength: edge_length * 3,
                gravity: -15,
                theta: 1,
                maxIterations: 3000,
                padding: 10,
                theta: 1,
                dragCoeff: 0.01,
                pull: 0.0001,
                nodeOverlap: 6,
                initialTemp: 2500,
                numIter: 2500,
                idealEdgeLength: edge_length,
                nodeDimensionsIncludeLabels: true
            },
            layout = cy_full.layout(layout_options),
            previousTapStamp;

        cy_full.fit();
        layout.run();


        cy_full.on('doubleTap', 'node', function(tap_event, event) {
            var tippyA = event.target.data("tippy");
            if (tippyA) {
                tippyA.hide();
                event.target.data("tippy", null);
            }
            event.target.addClass("active");
            if (typeof(event.target.data("expanded")) == "undefined") {
                $.getJSON(event.target.data("details"), function(new_elements) {
                    var root_position = cy_full.$("node[?is_main]").renderedPosition(),
                        pos = event.target.renderedPosition(),
                        misplaced_pos = {
                            x: pos.x + (pos.x - root_position.x) * 0.5,
                            y: pos.y + (pos.y - root_position.y) * 0.5
                        };
                    event.target.data("expanded", true);
                    for (var i = new_elements["nodes"].length - 1; i >= 0; i--) {
                        new_elements["nodes"][i]["data"]["parent_entity"] = event.target.id();
                    }
                    var eles = cy_full.add(new_elements);
                    if (eles.length > 0) {
                        eles.renderedPosition(misplaced_pos);
                        layout.stop();
                        layout = cy_full.layout(partial_layout_options);
                        layout.run();
                    }
                });
            }
        }).on('mouseover', 'node', function(event) {
            var outbound = cy_full.$('edge[source="' + event.target.id() + '"]'),
                inbound = cy_full.$('edge[target="' + event.target.id() + '"]'),
                connections = event.target.data("all_connected") || [],
                neighbours = [],
                connections_to_open = 0;
            inbound.addClass("active");
            outbound.addClass("active");
            inbound.forEach(function(edge) {
                neighbours.push(edge.data("source"));
            });
            outbound.forEach(function(edge) {
                neighbours.push(edge.data("target"));
            });
            for (var i = connections.length - 1; i >= 0; i--) {
                if (neighbours.indexOf(connections[i]) == -1) {
                    connections_to_open += 1;
                }
            }
            var tippyA = makeTippy(event.target, connections_to_open, "pep", "top");
            tippyA.show();
            event.target.data("tippy", tippyA);
        }).on('mouseout', 'node', function(event) {
            cy_full.$('edge[source="' + event.target.id() + '"], edge[target="' + event.target.id() + '"]').removeClass("active");
            var tippyA = event.target.data("tippy");
            if (tippyA) {
                tippyA.hide();
                event.target.data("tippy", null);
            }
        }).on('mouseover', 'edge', function(event) {
            event.target.addClass("hover");
        }).on('mouseout', 'edge', function(event) {
            event.target.removeClass("hover");
        }).on('tap', function(e) {
            var currentTapStamp = e.timeStamp;
            var msFromLastTap = currentTapStamp - previousTapStamp;
            if (msFromLastTap < 250) {
                e.target.trigger('doubleTap', e);

                var tippyPopoverToRemove = e.target.data("tippy_popover");
                if (tippyPopoverToRemove) {
                    tippyPopoverToRemove.hide();
                    e.target.data("tippy_popover", null);
                }
            } else {

                cy_full.$(".has_popover").forEach(function(node){
                    var tippyPopoverToRemove = node.data("tippy_popover");
                    if (tippyPopoverToRemove) {
                        tippyPopoverToRemove.hide();
                        node.data("tippy_popover", null);
                    }
                });

                if (e.target.isNode()) {
                    var tippyPopover = makeTippy(e.target,
                        '<a href="' + e.target.data("url") + '" target="_blank">' + e.target.data("full_name") + '</a><br />' + e.target.data("kind") + "<br/>" + e.target.data("description"), "light", "right");

                    tippyPopover.show();
                    e.target.addClass("has_popover");
                    e.target.data("tippy_popover", tippyPopover);
                }
            }
            previousTapStamp = currentTapStamp;
        });
    }
 
    $(".visualization-btn").on("click", function(e) {
        e.preventDefault();

        var anchor = $(this).data("target");
        $("#visualization-modal").addClass("modal--open");
        $.getJSON($(this).closest("button").data("url"), function(elements) {
            init_full(elements);
        });
    });
});