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
        if (teamName.trim().length > 0){
          $('#create_team').submit();
        }
        else {
          $('section').prepend('<h3 class="error">Team name is mandatory</h3>');
          // $('.error').css('display','block');
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

    $('.fixture').delegate('td.action_link', 'click', function() {
      $this = $(this);
      var action_type = $this.find('a').text();
      if (action_type === 'Edit'){
        // alert(action_type);
        $(this).closest('tr').css('background-color','#44c154').find('input').prop('disabled', false);
        $(this).after('<td class="action_link"><a class="AL_cancel" href="#">Cancel</a></td>');
        $(this).after('<td class="action_link"><a class="AL_save" href="#">Save</a></td>');
        // alert($(this).parent());
        // console.log($(this).parent());
        $(this).remove();} //end if action type is *EDIT*
        if (action_type === 'Cancel'){
          // alert(action_type);
          $(this).closest('tr').css('background-color','#e8f7f3').find('input').prop('disabled', true).val('0');
          $(this).after('<td class="action_link"><a class="AL_edit" href="#">Edit</a></td>');
          $(this).closest('tr').find('td:nth-child(7)').remove();
          $(this).closest('tr').find('td:nth-child(7)').remove();
        } //end if action type is *CANCEL*
        if (action_type === 'Save'){
          alert(action_type);
        } //end if action type is *SAVE*
    }); //function end

    var team = $('#team_details_name').text();
    $("tr.result_row").each(function() {
      // alert(team + '\n' + row_team);
      $this = $(this);
      var row_team = $this.find("td.home_team").text();
      var home = $this.find("td.home").text();
      var away = $this.find("td.away").text();
      if (row_team === team){
        if (home > away) {
          $(this).find('td.result_type').append('<img src="/static/images/win.png"/>');
        } else if (away > home) {
          $(this).find('td.result_type').append('<img src="/static/images/loss.png"/>');
        } else {
          $(this).find('td.result_type').append('<img src="/static/images/draw.png"/>');
        }
      }
      if (row_team != team) {
        if (home > away) {
          $(this).find('td.result_type').append('<img src="/static/images/loss.png"/>');
        } else if (away > home) {
          $(this).find('td.result_type').append('<img src="/static/images/win.png"/>');
        } else {
          $(this).find('td.result_type').append('<img src="/static/images/draw.png"/>');
        }
      }
    });

       $( ".selectmenu" ).selectmenu();
       $(".spinner").spinner({
          min: 0
       });

       $( "#menu" ).menu();
       $(" #GDToolTip ").tooltip();


      $('.error').fadeIn("slow");
      $('.feedback').fadeIn("slow");
      $('.warning').fadeIn("slow");

});//end top document.ready function

//set focus on team name input on create team form
// document.getElementById("teamName").focus();
