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
           $("#dialog-confirm").dialog({
             title: "save team?",
             resizable: false,
             //autoOpen: false,
             height: "auto",
             width: 400,
             modal: true,
             buttons: {
               "No, don't save team": function() {
                 $( this ).dialog( "close" );
               },
               "Yes, save team": function() {
                 $("#create_team").submit();
               }
             } //end buttons
           });
       });

       $( ".selectmenu" ).selectmenu();
       $(".spinner").spinner({
          min: 0
       });

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


     });//end top document.ready function

//set focus on team name input on create team form
document.getElementById("teamName").focus();
