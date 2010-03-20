window.addEvent('domready', function() {
    $$('.chooser').each(function(chooser) {
        
        // load all available options assigned to this chooser
        chooser.options = chooser.getElements('.option');

        // the first option should be the active one
        chooser.active = chooser.options[0];
    

        // Apply some properties to the options
        chooser.options.each(function(option) {
            // set the assigned chooser
            option.chooser = chooser;
            
            // on click this option should be set as active
            option.onclick = function() {
                if (option != option.chooser.active) {
                    option.chooser.set_active(option);
                }
            }
        })
            
        // Check if there is a tabs container assigned to this chooser
        tabs_container_id_wouldbe = chooser.id + '-tabs';
        chooser.has_tabs = $chk($(tabs_container_id_wouldbe));

        // if this chooser has tabs, do some initialization stuff
        if (chooser.has_tabs) {
            // Load all available tabs in the tabs container assigned to this chooser
            chooser.tabs = $(tabs_container_id_wouldbe).getElements('.tab');

            // apply some properties to the available tabs
            chooser.tabs.each(function(tab) {
                // assign the option that belongs to this tab 
                // (which has almost the same ID as this tab,
                // but it ends without the '-tab', so we'll remove it)
                tab.option = $(tab.id.replace('-tab', ''));
                tab.fade(0);
            });
        }

        chooser.set_active = function(option) {

            // first give all options the same class name
            this.options.each(function(option) {
                option.className = 'option';
            });

            // now add the class "active" to the option that shall be active
            option.chooser.active = option;
            option.className = 'option active';

            // if the chooser element of this option has tabs available,
            // set the tab which belongs to the option that shall be active, active too
            if (option.chooser.has_tabs) {
                this.tabs.each(function(tab){
                    // if the current tab is active, deactivate it
                    if (tab.className == 'tab active') {
                        tab.fade(0);
                        tab.className = 'tab';
                    }
                    // if the option of the current tab is the same as the one that shall be active,
                    // activate this tab
                    if (tab.option.id == option.id) {
                        tab.fade(1);
                        tab.className = 'tab active';
                    }
                });                
            }

            // ha! the active option has changed, so we have to emit a signal (which is an event in JS's case)
            option.chooser.fireEvent('value_changed', option);
        };
        
        chooser.set_active(chooser.active);
    });
});
