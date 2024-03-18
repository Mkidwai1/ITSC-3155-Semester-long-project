// Function to handle opening the navigation sidebar
function openNav() {
    document.getElementById("navbar").style.width = "250px";
}

// Function to handle closing the navigation sidebar
function closeNav() {
    document.getElementById("navbar").style.width = "0";
}

// Calendar JS logic below

console.log('FullCalendar is:', typeof FullCalendar !== 'undefined' ? 'Loaded' : 'Not loaded');

    document.addEventListener('DOMContentLoaded', function () {
        var calendarEl = document.getElementById('calendar');

        var calendar = new FullCalendar.Calendar(calendarEl, {
                schedulerLicenseKey: 'CC-Attribution-NonCommercial-NoDerivatives',
            initialView: 'dayGridMonth',
            initialDate: '2024-02-07',
            headerToolbar: {
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: [
                { title: 'Example Event', start: '2024-03-01' }
            ],
            dateClick: function(info) {
                var eventType = prompt("Enter event type (homework, class, project, meeting):");
                // Further logic based on eventType
            }
        });

        calendar.render();
    });
    console.log("after fullCalendar initilized");

// modal handling
document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        // ... FullCalendar initialization ...
        dateClick: function(info) {
            $('#eventModal').modal('show');
        }
    });

    // Handle event type change
    $('#eventType').on('change', function() {
        var selectedType = $(this).val();
        $('#dateGroup, #timeGroup, #locationGroup, #classGroup').hide();
        if (selectedType === 'homework' || selectedType === 'project') {
            $('#dateGroup, #classGroup').show();
        } else if (selectedType === 'class' || selectedType === 'meeting') {
            $('#timeGroup, #locationGroup').show();
        }
    }).trigger('change');

    // Handle saving event
    $('#saveEvent').on('click', function() {
        // Collect form data and create an event
        // Example:
        var eventData = {
            title: $('#eventType').val(),
            start: $('#dueDate').val() + 'T' + $('#eventTime').val()
            // More data collection based on form inputs
        };
        calendar.addEvent(eventData);
        $('#eventModal').modal('hide');
    });

    calendar.render();
});

