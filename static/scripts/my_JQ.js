$(document).ready(function() {
  $('#create_team').validate({
      messages: {
        team: 'Team name is mandatory'
      }
      /*showErrors() presents a message pane informing of the
      number of errors in the form*/
      //,
      // showErrors: function(errorMap, errorList) {
      //   $('#usr_messages').html('<p>The form contains '
      //   + this.numberOfInvalids()
      //   + ' errors:</p>').addClass('error');
      //   this.defaultShowErrors();
      // }
    });

    $('#submitSaveTeam').on('click', function(e) {
        e.preventDefault();
        if ( $('.error').length ){
          $('.error').remove();
        }
        var teamName = $('#teamName').val();
        // if (is_msg_displaying){
        //   alert("FROm IF" + is_msg_displaying)
        // }
        if (teamName.trim().length > 0){
          $('#create_team').submit();
        }
        else {
          $('section').prepend('<h3 class="error">Team name is mandatory</h3>');
        }
     });

    $('#submitDeleteAllTeams').on('click', function(e) {
           e.preventDefault();
           $("#dialog-confirm").dialog({
             title: "Delete all teams?",
             resizable: false,
             //autoOpen: false,
             height: "auto",
             width: 400,
             modal: true,
             buttons: {
               "No, do not delete all teams": function() {
                 $( this ).dialog( "close" );
               },
               "Yes, delete all teams": function() {
                 $("#deleteAllTeams").submit();
               }
             } //end buttons
           });
       });

       $( ".selectmenu" ).selectmenu();
       $(".spinner").spinner({
          min: 0
       });

       $(" #GDToolTip ").tooltip();

      //  $( "#autocomplete" ).autocomplete({
      //     source: $.getJSON($SCRIPT_ROOT + '/get_teams_autocompletion_data'),
      //     minLength: 2
      //   });

      var availableTags = [
        	"Sen City",
          "Arsenal",
          "Man City",
        	"Man Utd"
                      ];
      $( "#autocomplete" ).autocomplete({
      	source: availableTags
      });

      $('.feedback').fadeIn("slow");
      // $('.error').fadeIn("slow");

});//end top document.ready function

//set focus on team name input on create team form
document.getElementById("teamName").focus();
