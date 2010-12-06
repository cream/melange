var number_of_dialogs = 0;
var simple_dialog_overlay_id = 'simple-dialog-overlay'

function get_dialog_overlay() {
    if ($chk($(simple_dialog_overlay_id)) == false) {
        dialog_overlay = new Element('div', {
            'class': 'overlay',
            'id': simple_dialog_overlay_id
        });
    
        $$('.widget').grab(dialog_overlay, 'top');
    }
    else {
        dialog_overlay = $(simple_dialog_overlay_id);
    }
    
    return dialog_overlay;
}

function hide_all_dialogs() {
    $$('.simple-dialog').setStyle('display', 'none');
}

function chained_dialog_fadeout() {
    $(simple_dialog_overlay_id).fade('out');
    hide_all_dialogs();
}

var SimpleDialog = new Class({
    Implements: Options,
    
    options: {
        'alt_id': false,
        'ok_button_text': 'Ok',
        'cancel_button_text': 'Cancel',
        'ok_callback': function(){},
        'cancel_callback': function(){},
        'ok_callback_params_default': {},
        'cancel_callback_params_default': {}
    },

    initialize: function(options) {
        
        this.setOptions(options);
        
        number_of_dialogs++;
        
        this.dialog_id = this.options.alt_id ? this.options.alt_id : number_of_dialogs;
        
        // check if the dialog overlay already exists. otherwise create and inject it.
        this.dialog_overlay = get_dialog_overlay();
        
        // overlay should be hidden by default. always.
        this.dialog_overlay.fade('hide');
        this.dialog_overlay.setStyle('display', 'block');
        
        // wrapper for the dialog
        this.dialog_wrapper = new Element('div', {
            'class': 'simple-dialog',
            'id': 'dialog-' + this.dialog_id
        });
        
        // title/text for the dialog
        this.dialog_text_element = new Element('div', {
            'class': 'simple-dialog-text',
            'id': 'dialog-text-' + this.dialog_id
        });
        
        // button wrapper for the dialog
        this.dialog_button_wrapper = new Element('div', {
            'class': 'simple-dialog-buttons',
            'id': 'dialog-buttons-' + this.dialog_id
        });

        // "ok"-button for the dialog
        this.dialog_button_ok = new Element('div', {
            'class': 'button green',
            'id': 'dialog-ok-button-' + this.dialog_id,
            'text': this.options.ok_button_text
        });

        // "cancel"-button for the dialog
        this.dialog_button_cancel = new Element('div', {
            'class': 'button red',
            'id': 'dialog-cancel-button-' + this.dialog_id,
            'text': this.options.cancel_button_text
        });
        
        // dialog should be hidden by default
        this.dialog_wrapper.setStyle('display', 'none');
        
        // setting callback functions for the buttons
        this.dialog_button_ok.dialog_callback = this.options.ok_callback;
        this.dialog_button_cancel.dialog_callback = this.options.cancel_callback;
        
        // put buttons into wrapper
        this.dialog_button_wrapper.grab(this.dialog_button_ok);
        this.dialog_button_wrapper.grab(this.dialog_button_cancel);
        
        this.dialog_wrapper.grab(this.dialog_text_element);
        this.dialog_wrapper.grab(this.dialog_button_wrapper);
        
        // put dialog into the dialog overlay
        this.dialog_overlay.grab(this.dialog_wrapper);
        
        this.extra_buttons = new Array();
        
        // default callback params
        this.dialog_button_ok.dialog_callback_params = this.options.ok_callback_params_default;
        this.dialog_button_cancel.dialog_callback_params = this.options.cancel_callback_params_default;
        
        
        // OK click event
        this.dialog_button_ok.addEvent('click', function() {
            chained_dialog_fadeout();
            
            // call the callback of this button
            this.dialog_callback(this.dialog_callback_params);
        });
        
        // CANCEL click event
        this.dialog_button_cancel.addEvent('click', function() {
            chained_dialog_fadeout();
            
            // call the callback of this button
            this.dialog_callback(this.dialog_callback_params);
        });
    },
    
    show: function(text, callback_params_ok, callback_params_cancel, callback_params_extra_buttons) {
        this.dialog_text_element.set('text', text);
        
        // assign parameters for the button's callback functions
        this.dialog_button_ok.dialog_callback_params = callback_params_ok;
        this.dialog_button_cancel.dialog_callback_params = callback_params_cancel;
        
        if (this.extra_buttons.length > 0) {
            for (i=0; i<this.extra_buttons.length; i++) {
                btn = this.extra_buttons[i];
                btn.dialog_callback_params = callback_params_extra_buttons[i];
            }
        }
        
        this.dialog_wrapper.setStyle('display', 'block');
        this.dialog_overlay.fade('in');
    },
    
    add_button: function(button_text, callback, extra_classes) {
        button = new Element('div', {
            'class': 'button ' + extra_classes,
            'id': 'dialog-extra-button-' + (this.extra_buttons.length + 1),
            'text': button_text
        });
        
        button.dialog_callback = callback;
        button.dialog_callback_params = {};
        
        this.extra_buttons.push(button);
        
        this.dialog_button_wrapper.grab(button);
    },
    
    set_up_extrabuttons: function() {
        for (i=0; i<this.extra_buttons.length; i++) {
            btn = this.extra_buttons[i];
            
            btn.addEvent('click', function() {
                chained_dialog_fadeout();
                
                this.dialog_callback(this.dialog_callback_params);
            });
        }
    }
});
