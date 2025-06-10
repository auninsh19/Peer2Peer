// script.js

document.addEventListener('DOMContentLoaded', function() {
    // Select DOM elements
    const toggleButton = document.querySelector('.profile-toggle');
    const profileLinks = document.querySelector('.profile-links');
    const totalEvaluationsSpan = document.getElementById('total-evaluations');
    const completedEvaluationsSpan = document.getElementById('completed-evaluations');
    const assignmentSelect = document.getElementById('assignment-select');
    const memberSelect = document.getElementById('member-select');
    const evaluationForm = document.getElementById('evaluation-form');
    //const dynamicFields = document.getElementById('dynamic-fields');
    const selfEvaluationForm = document.getElementById('self-evaluation-form');
    const completedSelfEvaluation = {{ completed_self_evaluation is not none | tojson }};

    // Initialize evaluations object with data from the server
    const evaluations = {
        total: 0,
        completed: 0,
        members: [
            {% for member in group_members %}
                { id: "{{ member.user.id }}", name: "{{ member.user.name }}", completed: false },
            {% endfor %}
        ],
        assignments: [
            {% for assignment in assignments %}
                { id: "{{ assignment.id }}", title: "{{ assignment.title }}" },
            {% endfor %}
        ]
    };

    /*const questions = [
        {
            text: "How actively did your teammate contribute to group discussions and meetings?",
            scale: "1 (Low) - 5 (High)",
            name: "P1"
        },
        {
            text: "How frequently did your teammate share ideas and insights during group activities?",
            scale: "1 (Rarely) - 5 (Frequently)",
            name: "P2"
        },
        {
            text: "To what extent did your teammate engage in collaborative decision-making processes within the group?",
            scale: "1 (Not at all) - 5 (Extensively)",
            name: "P3"
        },
        {
            text: "Were their contributions constructive and beneficial to the group's progress?",
            scale: "1 (Not beneficial) - 5 (Highly beneficial)",
            name: "P4"
        },
        {
            text: "Did your teammate take on a leadership role within the group? If yes, how effective was their leadership?",
            scale: "1 (Ineffective) - 5 (Highly Effective)",
            name: "L1"
        }
        {
            text: "How well did your teammate guide and motivate the group toward achieving its goals?",
            scale: "1 (Poorly) - 5 (Exceptionally well)",
            name: "L2"
        },
        {
            text: "Did your teammate delegate tasks effectively and fairly?",
            scale: "1 (Ineffectively) - 5 (Effectively)",
            name: "L3"
        },
        {
            text: "Did your teammate participate in leading/facilitating discussion?",
            scale: "1 (Poorly) - 5 (Exceptionally well)",
            name: "L4"
        },
        {
            text: "How well did your teammate collaborate with others in the group?",
            scale: "1 (Poorly) - 5 (Excellent)",
            name: "C1"
        },
        {
            text: "Did your teammate actively seek and consider the opinions and ideas of other group members?",
            scale: "1 (Rarely) - 5 (Consistently)",
            name: "C2"
        },
        {
            text: "Were they receptive to feedback and willing to compromise when needed?",
            scale: "1 (Not receptive) - 5 (Very receptive)",
            name: "C3"
        },
        {
            text: "Did your teammate clearly understand their roles and their tasks?",
            scale: "1 (Poorly) - 5 (Excellent)",
            name: "C4"
        },
        {
            text: "How well did your teammate adhere to project deadlines and timelines?",
            scale: "1 (Frequently Missed) - 5 (Always Met)",
            name: "TM1"
        },
        {
            text: "Were there instances where your teammate's time management positively or negatively impacted the group's progress?",
            scale: "1 (Negatively) - 5 (Positively)",
            name: "TM2"
        },
        {
            text: "Did your teammate effectively communicate any challenges they faced in meeting deadlines?",
            scale: "1 (Poor communication) - 5 (Excellent communication)",
            name: "TM3"
        },
        {
            text: "Did your teammate attend group meetings regularly and arrive on time?",
            scale: "1(Poor) - 5(Excellent)",
            name: "TM4"
        },
        {
            text: "Evaluate your teammate's communication skills, considering clarity, active listening, and expression of ideas.",
            scale: "1 (Ineffective) - 5 (Highly Effective)",
            name: "Comm1"
        },
        {
            text: "Did your teammate effectively convey complex information or instructions to the group?",
            scale: "1 (Not effectively) - 5 (Very effectively)",
            name: "Comm2"
        },
        {
            text: "How responsive and open was your teammate to communication from other group members?",
            scale: "1 (Not responsive) - 5 (Very responsive)",
            name: "Comm3"
        },
        {
            text: "Was your teammate always open to receiving both negative and positive feedback from other teammates?",
            scale: "1(Poor) - 5(Excellent)",
            name: "Comm4"
        },
        {
            text: "How well did your teammate analyse challenges and propose solutions during the project?",
            scale: "1 (Poorly) - 5 (Exceptionally well)",
            name: "PS1"
        },
        {
            text: "Did they actively seek alternative solutions and consider different perspectives?",
            scale: "1 (Rarely) - 5 (Consistently)",
            name: "PS2"
        },
        {
            text: "Did your teammate address and resolve issues quickly?",
            scale: "1 (Poorly) - 5 (Exceptionally well)",
            name: "PS3"
        },
        {
            text: "Your teammate takes responsibility for the effectiveness of your team.",
            scale: "1 (Rarely) - 5 (Consistently)"
            name: "PS4"
        }
    ];*/

    // Toggle the display of the profile links
    toggleButton.addEventListener('click', function() {
        profileLinks.style.display = (profileLinks.style.display === 'none' || profileLinks.style.display === '') ? 'block' : 'none';
    });

    // Close the profile links if clicking outside
    document.addEventListener('click', function(event) {
        if (!toggleButton.contains(event.target) && !profileLinks.contains(event.target)) {
            profileLinks.style.display = 'none';
        }
    });

    // Function to update evaluation status dynamically
    function updateEvaluationStatus(completedCount) {
        completedEvaluationsSpan.innerText = completedCount;
    }

    // Example function to simulate updating completed evaluations
    function onEvaluationSubmit() {
        let currentCompleted = parseInt(completedEvaluationsSpan.innerText, 10);
        updateEvaluationStatus(currentCompleted + 1);
    }

    // Add event listeners to both dropdowns
    assignmentSelect.addEventListener('change', toggleEvaluationForm);
    memberSelect.addEventListener('change', function() {
        toggleEvaluationForm();
        //populateEvaluationFields(); // Populate fields when member changes
    });

    // Show the evaluation form only if both assignment and member are selected
    function toggleEvaluationForm() {
        // Show the evaluation form only if both assignment and member are selected
        if (assignmentSelect.value && memberSelect.value) {
            document.getElementById('evaluation-form').style.display = 'block'; // Show the evaluation form
        } else {
            document.getElementById('evaluation-form').style.display = 'none'; // Hide if either is not selected
        }       
    }

    // Populate evaluation fields based on selected member
    //function populateEvaluationFields() {
    //    dynamicFields.innerHTML = ''; // Clear previous fields

    //    if (memberSelect.value) {
    //        const memberId = memberSelect.value;
    //        const memberName = memberSelect.options[memberSelect.selectedIndex].text;

            // Loop through each question and create radio buttons
    //       questions.forEach(question => {
    //            dynamicFields.innerHTML += `<p>${question.text}</p>`;
    //            dynamicFields.innerHTML += `<p style="font-size: 14px; color: green;">${question.scale}</p>`;
    //            dynamicFields.innerHTML += `<div class="radio-group">`;
    //            for (let i = 1; i <= 5; i++) {
    //                dynamicFields.innerHTML += `
    //                    <label>
    //                        <input type="radio" name="${question.name}_${memberId}" value="${i}" required> ${i}
    //                    </label>
    //                `;
    //            }
    //        });

    //        document.getElementById('evaluation-form').style.display = 'block'; // Show the evaluation form
    //    } else {
    //        document.getElementById('evaluation-form').style.display = 'none'; // Hide if no member is selected
    //    }
    //}

    // Initial call to set the evaluation status
    updateEvaluationStatus();
});




<h3>Participation:</h3>
                        <p>How actively did your teammate contribute to group discussions and meetings?</p>
                        <p style="font-size: 14px; color: green;">1 (Low) - 5 (High)</p>

                        <div class="radio-group">
                            {% for i in range(1,6) %}
                                <label>
                                    <input type="radio" name="P1_{{ member.user.id }}" value="{{ i }}" required> {{ i }}
                                </label>
                            {% endfor %}
                        </div>                   
                    
                        <br><br>

                        <p>How frequently did your teammate share ideas and insights during group activities?</p>
                        <p style="font-size: 14px; color: green;">1 (Rarely) - 5 (Frequently)</p>
                        <div class="radio-group">
                            {% for i in range(1,6) %}
                                <label>
                                    <input type="radio" name="P2_{{ member.user.id }}" value="{{ i }}" required> {{ i }}
                                </label>
                            {% endfor %}
                        </div>
                        
                        <br><br>

                        <p>To what extent did your teammate engage in collaborative decision-making processes within the group?</p>
                        <p style="font-size: 14px; color: green;">1 (Not at all) - 5 (Extensively)</p>
                        <div class="radio-group">
                            {% for i in range(1,6) %}
                                <label>
                                    <input type="radio" name="P3_{{ member.user.id }}" value="{{ i }}" required> {{ i }}
                                </label>
                            {% endfor %}
                        </div>
                    
                        <br><br>

                        <p>Were their contributions constructive and beneficial to the group's progress?</p>
                        <p style="font-size: 14px; color: green;">1 (Not beneficial) - 5 (Highly beneficial)</p>
                        <div class="radio-group">
                            {% for i in range(1,6) %}
                                <label>
                                    <input type="radio" name="P4_{{ member.user.id }}" value="{{ i }}" required> {{ i }}
                                </label>
                            {% endfor %}
                        </div>

                        <br><br>

                        <hr>