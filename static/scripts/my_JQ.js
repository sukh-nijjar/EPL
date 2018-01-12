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

    // update to accept any TR and render edit mode accordingly
    // which includes updating scores with goals values already set
    $('tr').delegate('td.action_link', 'click', function(e) {
      $this = $(this);
      var action_type = $this.find('a').text();
      if (action_type === 'Edit'){
          if ($(this).closest('tr').hasClass('fixture')){
            alert("Fixture class row");
            $(this).closest('tr').css('background-color','#44c154').find('input').prop('disabled', false);
            $(this).after('<td class="action_link"><a class="AL_cancel" href="#">Cancel</a></td>');
            $(this).after('<td class="action_link"><a class="AL_save" href="#">Save</a></td>');
            // console.log($(this).parent());
            $(this).remove();
          } else {
            alert("It's a result class row");
          }
        } //end if action type is *EDIT*
        if (action_type === 'Cancel'){
          location.reload(true);
          // alert(action_type);
          // $(this).closest('tr').css('background-color','#e8f7f3').find('input').prop('disabled', true).val('0');
          // $(this).after('<td class="action_link"><a class="AL_edit" href="#">Edit</a></td>');
          // $(this).closest('tr').find('td:nth-child(7)').remove();
          // $(this).closest('tr').find('td:nth-child(7)').remove();
        } //end if action type is *CANCEL*
        if (action_type === 'Save'){
          var r = $(this).closest('tr');
          // console.log(r);
          $.ajax({
            data :  {
              home_team : $(this).closest('tr').find('[name=home_team]').text(),
              hftg : $(this).closest('tr').find('td input[name=hftg]').val(),
              hhtg : $(this).closest('tr').find('td input[name=hhtg]').val(),
              ahtg : $(this).closest('tr').find('td input[name=ahtg]').val(),
              aftg : $(this).closest('tr').find('td input[name=aftg]').val(),
              away_team : $(this).closest('tr').find('[name=away_team]').text()
            },
            type : 'POST',
            url : '/update_score/'
          })
          .done(function(data) {
            if (data.done) {
              alert(data.done);
              location.reload(true);
              // $(this).closest(r).removeClass('fixture');
              // $(r).removeClass('fixture').css('background-color','#ffffff');
            }
            else {
              alert(data.error);
            }
          })
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

function submit_inline_result(){
  // alert('Hello from inline');
  // var hftg = $(this).closest('tr').find('td:nth-child(2)').val();
  // alert(hftg);
}

//set focus on team name input on create team form
// document.getElementById("teamName").focus();
