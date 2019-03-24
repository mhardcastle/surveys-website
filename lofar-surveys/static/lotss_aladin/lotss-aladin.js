//
// Extensions to Aladin-lite to show the status of
// the LOFAR Survey (LoTTS).
// Stephen Bourke
// Onsala Space Observatory / Chalmers
//

var lotss_aladin = function(aladin_div, requestedOptions) {

    Aladin.DEFAULT_OPTIONS.target = "195 +48";
    Aladin.DEFAULT_OPTIONS.fov = 150;
    Aladin.DEFAULT_OPTIONS.survey = "P/TGSSADR";
    Aladin.DEFAULT_OPTIONS.lotss_pointings_url = "http://skogul.oso.chalmers.se/Lofar_Tier1_Survey/status/pointings_db.json";
    Aladin.DEFAULT_OPTIONS.lotss_pointings_radius = 1.65;
    HpxImageSurvey.SURVEYS.push(
        {
           "id": 'P/TGSSADR',
           "url": "http://tgssadr.strw.leidenuniv.nl/hips",
           "name": 'TGSS-ADR',
           "maxOrder": 7,
           "frame": 'equatorial',
           "format":'png'
        },
        {
           "id": 'LoTSSDR1',
           "url": "https://lofar-surveys.org/public/HIPS/low_hips/",
           "name": 'LoTSS-DR1-low',
           "maxOrder": 7,
           "frame": 'equatorial',
           "format":'png'
        },
	{
           "id": 'LoTSSDR1-high',
           "url": "https://lofar-surveys.org/public/HIPS/high_hips_new/",
           "name": 'LoTSS-DR1-high',
           "maxOrder": 7,
           "frame": 'equatorial',
           "format":'png'
        }

    );
    
    var aladin = A.aladin(aladin_div, requestedOptions);

    var overlay_colours = {
        RED: '#c35f5f',
        GREEN: '#5cc15a',
        BLUE: '#3a89c3',
        YELLOW: '#c3bf5f',
        DARK_BLUE: '#404080',
        GREY: '#c0c0c0',
        BLACK: '#222222',
        PURPLE: '#a000a0'
    };

    var colours_standard = function () {
        var colour_scheme = {
            Done: overlay_colours.GREEN,
            Failed: overlay_colours.BLUE,
            Ready: overlay_colours.BLUE,
            Observed: overlay_colours.BLUE,
            Scheduled: overlay_colours.YELLOW,
            Other: overlay_colours.BLUE,
            Not_Observed: overlay_colours.RED,
        };

        var create_key = function() {
            return '<div style="width: 10px; height: 10px; background: ' + overlay_colours.GREEN + '; float: left; margin: 2px; margin-right: 8px;" />Processed<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + overlay_colours.BLUE + '; float: left; margin: 2px; margin-right: 8px;" />Observed<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + overlay_colours.YELLOW + '; float: left; margin: 2px; margin-right: 8px;" />Scheduled<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + overlay_colours.RED + '; float: left; margin: 2px; margin-right: 8px;" />Not Started&nbsp;<br/>';

        }
        colour_scheme.create_key = create_key;
        return colour_scheme;
    }();

    var colours_alt = function () {
        var colour_scheme = {
            Done: overlay_colours.GREEN,
            Failed: overlay_colours.RED,
            Ready: overlay_colours.BLACK,
            Observed: overlay_colours.GREY,
            Scheduled: overlay_colours.YELLOW,
            Other: overlay_colours.PURPLE,
            Not_Observed: overlay_colours.DARK_BLUE
        }

        var create_key = function() {
            return '<div style="width: 10px; height: 10px; background: ' + colour_scheme.Done + '; float: left; margin: 2px; margin-right: 8px;" />Done<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + colour_scheme.Failed + '; float: left; margin: 2px; margin-right: 8px;" />Failed<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + colour_scheme.Ready + '; float: left; margin: 2px; margin-right: 8px;" />Ready<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + colour_scheme.Observed + '; float: left; margin: 2px; margin-right: 8px;" />Observed<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + colour_scheme.Scheduled + '; float: left; margin: 2px; margin-right: 8px;" />Scheduled<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + colour_scheme.Other + '; float: left; margin: 2px; margin-right: 8px;" />Other<br/>' +
                   '<div style="width: 10px; height: 10px; background: ' + colour_scheme.Not_Observed + '; float: left; margin: 2px; margin-right: 8px;" />Not Observed&nbsp;<br/>';

        }
        colour_scheme.create_key = create_key;
        return colour_scheme;
    }();

    var colours = colours_standard;
    if (localStorage["use_alt_colours"] === undefined) {
        localStorage["use_alt_colours"] = JSON.stringify(false);
    }
    if (JSON.parse(localStorage["use_alt_colours"])) {
        colours = colours_alt;
    }

    var popup = function(name, pstatus, obs) {
        // Generate an Aladin catalog popup for the pointing with
        // information on observations is present
        if (obs.length == 0) {
            return {popupTitle: name};
        } else {
            desc = "Pipeline Status: " + pstatus + "<br>Observations:";
            for (var i = 0; i < obs.length; i++) {
                desc = desc + "<br>&nbsp;&nbsp;Obs ID: " + obs[i].id;
                desc = desc + "<br>&nbsp;&nbsp;Obs Date: " + obs[i].date;
                desc = desc + "<br>&nbsp;&nbsp;Status: " + obs[i].status;
                desc = desc + "<br>";
            }
            return {popupTitle: name, popupDesc: desc};
        }
    };

    var overlay_started;
    var overlay_not_started;
    var markers_started;
    var markers_not_started;

    var create_overlays = function() {
        // Add overlays for the FoV circles
        overlay_started = A.graphicOverlay({name: "Started (circles)", color: '#eee'});
        aladin.addOverlay(overlay_started);
        overlay_not_started = A.graphicOverlay({name: "Not Started (circles)", color: '#eee'});
        aladin.addOverlay(overlay_not_started);
        
        // Add 'catalogs' for popup markers.
        markers_started = A.catalog({name: 'Started (Info Popups)', sourceSize: 10, color: '#eee'});
        aladin.addCatalog(markers_started);
        markers_not_started = A.catalog({name: 'Not Started (Info Popups)', sourceSize: 10, color: '#eee'});
        aladin.addCatalog(markers_not_started);
    };

    var clear_overlays = function() {
        // Remove any pointings that were added.
        overlay_started.overlay_items = [];
        overlay_not_started.overlay_items = [];
        markers_started.sources = [];
        markers_not_started.sources = [];
    };

    var add_pointing = function(pointing) {
        // Add a circle and popup link for a pointing.
        // 'pointing' is an array of length 5: [name, ra, dec, status, [obs]].
        // [obs] is an array of observations data.
        var name = pointing[0];
        var ra = pointing[1];
        var dec = pointing[2];
        var pstatus = pointing[3];
        var obs = pointing[4];
        var radius = aladin.options.lotss_pointings_radius;
        if (obs.length > 0) {
            var circle_props = {color: colours[pstatus], lineWidth: 1};
            overlay_started.add(A.circle(ra, dec, radius, circle_props));
            markers_started.addSources([A.marker(ra, dec, popup(name, pstatus, obs))]);
        } else {
            var circle_props = {color: colours[pstatus], lineWidth: 1};
            overlay_not_started.add(A.circle(ra, dec, radius, circle_props));
            markers_not_started.addSources([A.marker(ra, dec, {popupTitle: name})]);
        }
    };
    
    var json_data;
    var add_survey_pointings = function() {
        // Get the pointings information and add it to the plugin.
        if (json_data === undefined) {
            $.getJSON(aladin.options.lotss_pointings_url).done(
                function(response) {
                    json_data = response;
                    $.each(response, function (i, pointing) {
                        add_pointing(pointing);
                    });
            });
        } else {
            $.each(json_data, function (i, pointing) {
                add_pointing(pointing);
            });
        }
        updateFovDiv(aladin.view);
    };
    aladin.add_survey_pointings = add_survey_pointings;


    // Override the Aladin global function updateFovDiv to add colour key
    updateFovDiv = function(view) {
	    if (isNaN(view.fov)) {
	        view.fovDiv.html("FoV:");
	        return;
	    }
        // update FoV value
        var fovStr;
        if (view.fov>1) {
            fovStr = Math.round(view.fov*100)/100 + "°";
        }
        else if (view.fov*60>1) {
            fovStr = Math.round(view.fov*60*100)/100 + "'";
        }
        else {
            fovStr = Math.round(view.fov*3600*100)/100 + '"';
        }
        view.fovDiv.html(colours.create_key() + "FoV: " + fovStr);
	};
    

    aladin.overlayByName = function(name) {
        return this.view.overlays.filter(function(overlay) {
            return overlay.name === name;
        })[0];
    };
    
    
    // This is a modfied version of the AladinLite method
    // responsible for handling layers.
    // It is modified to provide an alternative colour
    // scheme. Search below for SurveySearch.
    //
    // NOTE: This is based on AladinLite-2018-10-30
    aladin.showLayerBox = function() {
        var self = this;
        
        // first, update
        var layerBox = $(this.aladinDiv).find('.aladin-layerBox');
        layerBox.empty();
        layerBox.append('<a class="aladin-closeBtn">&times;</a>' +
                '<div style="clear: both;"></div>' +
                '<div class="aladin-label">Base image layer</div>' +
                '<select class="aladin-surveySelection"></select>' +
                '<div class="aladin-cmap">Color map:' +
                '<div><select class="aladin-cmSelection"></select><button class="aladin-btn aladin-btn-small aladin-reverseCm" type="button">Reverse</button></div></div>' +
                '<div class="aladin-box-separator"></div>' +
                '<div class="aladin-label">Overlay layers</div>');
        
        var cmDiv = layerBox.find('.aladin-cmap');
        
        // fill color maps options
        var cmSelect = layerBox.find('.aladin-cmSelection');
        for (var k=0; k<ColorMap.MAPS_NAMES.length; k++) {
            cmSelect.append($("<option />").text(ColorMap.MAPS_NAMES[k]));
        }
        cmSelect.val(self.getBaseImageLayer().getColorMap().mapName);

        
        // loop over all overlay layers
        var layers = this.view.allOverlayLayers;
        var str = '<ul>';
        for (var k=layers.length-1; k>=0; k--) {
            var layer = layers[k];
            var name = layer.name;
            var checked = '';
            if (layer.isShowing) {
                checked = 'checked="checked"';
            }

            var tooltipText = '';
            var iconSvg = '';
            if (layer.type=='catalog' || layer.type=='progressivecat') {
               var nbSources = layer.getSources().length;
               tooltipText = nbSources + ' source' + ( nbSources>1 ? 's' : '');

               iconSvg = AladinUtils.SVG_ICONS.CATALOG;
           }
           else if (layer.type=='moc') {
               tooltipText = 'Coverage: ' + (100*layer.skyFraction()).toFixed(3) + ' % of sky';

               iconSvg = AladinUtils.SVG_ICONS.MOC;
           }
           else if (layer.type=='overlay') {
               iconSvg = AladinUtils.SVG_ICONS.OVERLAY;
           }

            var rgbColor = $('<div></div>').css('color', layer.color).css('color'); // trick to retrieve the color as 'rgb(,,)' - does not work for named colors :(
            var labelColor = Color.getLabelColorForBackground(rgbColor);

            // retrieve SVG icon, and apply the layer color
            var svgBase64 = window.btoa(iconSvg.replace(/FILLCOLOR/g, layer.color));
            str += '<li><div class="aladin-stack-icon" style=\'background-image: url("data:image/svg+xml;base64,' + svgBase64 + '");\'></div>';
           str += '<input type="checkbox" ' + checked + ' id="aladin_lite_' + name + '"></input><label for="aladin_lite_' + name + '" class="aladin-layer-label" style="background: ' + layer.color + '; color:' + labelColor + ';" title="' + tooltipText + '">' + name + '</label></li>';
        }
        str += '</ul>';
        layerBox.append(str);
        
        layerBox.append('<div class="aladin-blank-separator"></div>');
        
        // SurvayStatus modification
        // Handle alternative colour scheme
        var checked = '';
        if (JSON.parse(localStorage["use_alt_colours"])) {
            checked = 'checked';
        }
        var altColoursCb = $('<input type="checkbox" ' + checked + ' id="displayAltColours" />');
        layerBox.append(altColoursCb).append('<label for="displayAltColours">Alternative Colours</label><br/>');
        altColoursCb.change(function() {
            if ($(this).is(':checked')) {
                localStorage["use_alt_colours"] = JSON.stringify(true);
                colours = colours_alt;
                clear_overlays();
                add_survey_pointings();
            } else {
                localStorage["use_alt_colours"] = JSON.stringify(false);
                colours = colours_standard;
                clear_overlays();
                add_survey_pointings();
            }
        });
        // End of this SurvayStatus modification

        // gestion du réticule
        var checked = '';
        if (this.view.displayReticle) {
            checked = 'checked="checked"';
        }
        var reticleCb = $('<input type="checkbox" ' + checked + ' id="displayReticle" />');
        layerBox.append(reticleCb).append('<label for="displayReticle">Reticle</label><br/>');
        reticleCb.change(function() {
            self.showReticle($(this).is(':checked'));
        });
        
        // Gestion grille Healpix
        checked = '';
        if (this.view.displayHpxGrid) {
            checked = 'checked="checked"';
        }
        var hpxGridCb = $('<input type="checkbox" ' + checked + ' id="displayHpxGrid"/>');
        layerBox.append(hpxGridCb).append('<label for="displayHpxGrid">HEALPix grid</label><br/>');
        hpxGridCb.change(function() {
            self.showHealpixGrid($(this).is(':checked'));
        });
        
        
        layerBox.append('<div class="aladin-box-separator"></div>' +
             '<div class="aladin-label">Tools</div>');
        var exportBtn = $('<button class="aladin-btn" type="button">Export view as PNG</button>');
        layerBox.append(exportBtn);
        exportBtn.click(function() {
            self.exportAsPNG();
        });
                
                /*
                '<div class="aladin-box-separator"></div>' +
                '<div class="aladin-label">Projection</div>' +
                '<select id="projectionChoice"><option>SINUS</option><option>AITOFF</option></select><br/>'
                */

        layerBox.find('.aladin-closeBtn').click(function() {self.hideBoxes();return false;});
        
        // update list of surveys
        this.updateSurveysDropdownList(HpxImageSurvey.getAvailableSurveys());
        var surveySelection = $(this.aladinDiv).find('.aladin-surveySelection');
        surveySelection.change(function() {
            var survey = HpxImageSurvey.getAvailableSurveys()[$(this)[0].selectedIndex];
            self.setImageSurvey(survey.id, function() {
                var baseImgLayer = self.getBaseImageLayer();
                
                if (baseImgLayer.useCors) {
                    // update color map list with current value color map
                    cmSelect.val(baseImgLayer.getColorMap().mapName);
                    cmDiv.show();
                    
                    exportBtn.show();
                }
                else {
                    cmDiv.hide();
                    
                    exportBtn.hide();
                }
            });

            
            
        });
        
        //// COLOR MAP management ////////////////////////////////////////////
        // update color map
        cmDiv.find('.aladin-cmSelection').change(function() {
            var cmName = $(this).find(':selected').val();
            self.getBaseImageLayer().getColorMap().update(cmName);
        });
        
        // reverse color map
        cmDiv.find('.aladin-reverseCm').click(function() {
            self.getBaseImageLayer().getColorMap().reverse(); 
        });
        if (this.getBaseImageLayer().useCors) {
            cmDiv.show();
            exportBtn.show();
        }
        else {
            cmDiv.hide();
            exportBtn.hide();
        }
        layerBox.find('.aladin-reverseCm').parent().attr('disabled', true);
        //////////////////////////////////////////////////////////////////////
        
        
        // handler to hide/show overlays
        $(this.aladinDiv).find('.aladin-layerBox ul input').change(function() {
            var layerName = ($(this).attr('id').substr(12));
            var layer = self.layerByName(layerName);
            if ($(this).is(':checked')) {
                layer.show();
            }
            else {
                layer.hide();
            }
        });
        
        // finally show
        layerBox.show();
        
    };
     
    create_overlays();
    add_survey_pointings();
    
    return aladin;
};
