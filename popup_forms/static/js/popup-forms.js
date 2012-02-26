/* 
 * 
 * Script for managing Popup forms
 * 
 */

$(function() {
    /* Hide form content and show "progress" gif on submitting */
    $('div.popup_box form').submit(function() {
        $(this).parents('div.popup_container').addClass('loading');
        $(this).addClass('invisible');
    });

    /* Show the form by clicking on popup link */
    $('a.popup_form_link').click(function() {
        var form_item = $('#form_' + $(this).attr('id'));
        if (!form_item.is(':visible')) {
            $('div.popup_box').hide();
            form_item.appendTo('body');
            form_item.center();
            form_item.fadeIn('fast');
        }

        return false;
    });

    /* Fade-in and center a form, that is not hidden */
   $('div.popup_box:visible').each(function(){
       $(this).appendTo('body');
       $(this).center();
   });

    /* Hide all forms on clicking "close" button */
    $('div.popup_box .btn_popup_close').click(function() {
        $('div.popup_box').hide();
        return false;
    });

});

jQuery.fn.center = function () {
    this.css("position","absolute");
    this.css("top", (($(window).height() - this.outerHeight()) / 2) + $(window).scrollTop() + "px");
    this.css("left", (($(window).width() - this.outerWidth()) / 2) + $(window).scrollLeft() + "px");

    /* Prevent Firefox caching JS state of page
     * https://developer.mozilla.org/En/Using_Firefox_1.5_caching */
    $(window).unload(function() {});

    return this;
};