window.addEvent('domready', function() {
    $$('.chooser').each(function(chooser) {
        chooser.set_active = function(option) {
            this.options.each(function(option) {
                option.className = 'option';
                });
            option.chooser.active = option;
            option.className = 'option active';
            option.chooser.fireEvent('value_changed', option);
            };
    
        chooser.options = chooser.getElements('.option');
        chooser.active = chooser.options[0];
    
        chooser.options.each(function(option) {
            option.chooser = chooser;
            option.onclick = function() {
                if (option != option.chooser.active) {
                    option.chooser.set_active(option);
                    }
                }
            })
    
        chooser.set_active(chooser.active);
        });
    });
