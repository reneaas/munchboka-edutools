// munchboka-edutools quiz runtime
// Combines SequentialMultipleChoiceQuiz and MultipleChoiceQuestion with minimal deps.

// Generate UUID function
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0,
      v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function shuffleArray(array) {
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
}

class MultipleChoiceQuestion {
  constructor({ id, content, answers }) {
    this.id = id;
    this.content = content;
    this.answers = answers.map((answer) => {
      if (!Object.prototype.hasOwnProperty.call(answer, 'id')) {
        answer.id = generateUUID();
      }
      return answer;
    });
    this.selectedAnswers = new Set();
    this.elements = {}; // Store elements for easy access
    this.correctlyAnswered = false; // Track if the question is correctly answered
  }

  shuffleAnswers() {
    shuffleArray(this.answers);
  }

  render(containerId) {
    const container = document.getElementById(containerId);

    // Create question element
    const questionCard = document.createElement('div');
    questionCard.classList.add('question-card');
    questionCard.innerHTML = this.content;

    // Append the question card to the container
    container.appendChild(questionCard);

    // Render LaTeX in the question
    this.renderMathInElement(questionCard);

    // Apply syntax highlighting to the question card
    this.applySyntaxHighlighting(questionCard);

    // Create answers container
    const answersGrid = document.createElement('div');
    answersGrid.classList.add('answers-grid');

    // Append the answers grid to the container
    container.appendChild(answersGrid);

    // Create answer elements
    this.answers.forEach((answer) => {
      const answerCard = document.createElement('div');
      answerCard.classList.add('answer-card');
      answerCard.innerHTML = answer.content;
      answerCard.dataset.answerId = answer.id;

      // Append the answer card to the answers grid
      answersGrid.appendChild(answerCard);

      // Render LaTeX in the answer
      this.renderMathInElement(answerCard);

      // Apply syntax highlighting to the answer card
      this.applySyntaxHighlighting(answerCard);

      // Mark as selected if previously selected
      if (this.selectedAnswers.has(answer.id)) {
        answerCard.classList.add('selected');
      }

      // Disable interaction if question is correctly answered
      if (this.correctlyAnswered) {
        answerCard.classList.add('disabled');
      } else {
        // Add click event to handle selection
        answerCard.addEventListener('click', () => this.toggleSelection(answerCard));
      }
    });

    // Store elements for later access
    this.elements.container = container;
    this.elements.questionCard = questionCard;
    this.elements.answersGrid = answersGrid;

    // Apply correct class if previously answered correctly
    if (this.correctlyAnswered) {
      this.elements.questionCard.classList.add('correct');
    }
  }

  toggleSelection(answerCard) {
    const answerId = answerCard.dataset.answerId;
    if (this.selectedAnswers.has(answerId)) {
      this.selectedAnswers.delete(answerId);
      answerCard.classList.remove('selected');
    } else {
      // If single-choice, deselect other answers
      if (this.isSingleChoice()) {
        this.selectedAnswers.clear();
        const allAnswerCards = this.elements.answersGrid.querySelectorAll('.answer-card');
        allAnswerCards.forEach((card) => card.classList.remove('selected'));
      }
      this.selectedAnswers.add(answerId);
      answerCard.classList.add('selected');
    }
  }

  checkAnswers(showAlert = true) {
    // Get the correct answer IDs
    const correctAnswerIds = this.answers.filter((answer) => answer.isCorrect).map((answer) => answer.id);

    // Compare selectedAnswers with correctAnswerIds
    const isCorrect = this.selectedAnswers.size === correctAnswerIds.length && [...this.selectedAnswers].every((id) => correctAnswerIds.includes(id));

    // Provide visual feedback
    if (isCorrect) {
      this.elements.questionCard.classList.remove('incorrect'); // ✅ Remove incorrect class
      this.elements.questionCard.classList.add('correct');
      this.correctlyAnswered = true; // Mark question as correctly answered
      // Disable further interaction
      const allAnswerCards = this.elements.answersGrid.querySelectorAll('.answer-card');
      allAnswerCards.forEach((card) => {
        card.classList.add('disabled');

        const newCard = card.cloneNode(true);
        card.parentNode.replaceChild(newCard, card);
      });
    } else {
      this.elements.questionCard.classList.add('incorrect');
    }

    // Optionally display feedback if showAlert is true
    if (showAlert) {
      // eslint-disable-next-line no-alert
      alert(isCorrect ? 'Riktig!' : 'Feil. Prøv igjen.');
    }

    return isCorrect;
  }

  markAsCorrectlyAnswered() {
    this.correctlyAnswered = true;
  }

  isSingleChoice() {
    // Determine if the question is single-choice
    const correctAnswersCount = this.answers.filter((answer) => answer.isCorrect).length;
    return correctAnswersCount === 1;
  }

  renderMathInElement(element) {
    // Ensure KaTeX renders LaTeX inside the element
    if (typeof window !== 'undefined' && typeof window.renderMathInElement === 'function') {
      window.renderMathInElement(element, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\[', right: '\\]', display: true },
          { left: '\\(', right: '\\)', display: false },
        ],
      });
    }
  }

  applySyntaxHighlighting(element) {
    // Apply syntax highlighting to code blocks if highlight.js is present
    if (typeof window !== 'undefined' && window.hljs && typeof window.hljs.highlightElement === 'function') {
      const codeBlocks = element.querySelectorAll('code');
      codeBlocks.forEach((block) => {
        window.hljs.highlightElement(block);
      });
    }
  }
}

class SequentialMultipleChoiceQuiz {
  constructor(containerId, questionsData) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    if (!this.container) {
      throw new Error('Container not found');
    }
    this.questionsData = questionsData;
    this.totalQuestions = questionsData.length;
    this.currentQuestionIndex = 0;
    this.uniqueId = generateUUID();
    this.correctlyAnsweredQuestions = new Set(); // Track correctly answered questions
    this.questionInstances = {}; // Store instances of MultipleChoiceQuestion
    this.isFinished = false; // Track completion without destroying UI
    this.init();
  }

  init() {
    this.generateHTML();
    this.showQuestion();
  }

  generateHTML() {
    // Set up the main structure with Previous and Next buttons
    this.container.innerHTML = `
            <div id="question-counter-${this.uniqueId}" class="question-counter"></div>
            <div id="question-container-${this.uniqueId}" class="mcq-container"></div>
            <div class="button-container">
                <button id="prev-question-${this.uniqueId}" class="button button-prev">← Forrige</button>
                <button id="submit-answer-${this.uniqueId}" class="button button-run">Sjekk svar</button>
                <button id="next-question-${this.uniqueId}" class="button button-next">Neste →</button>
            </div>
            <div id="quiz-completion-${this.uniqueId}" class="quiz-completion-message" style="display: none;">
                <p>Da var quizen ferdig! 🎉</p>
            </div>
            <!-- Toast Notifications -->
            <div id="toast-success-${this.uniqueId}" class="toast toast-success" style="display: none;">
                <p>Riktig! 🎉</p>
            </div>
            <div id="toast-error-${this.uniqueId}" class="toast toast-error" style="display: none;">
                <p>Prøv igjen!</p>
            </div>
        `;

    // Add event listeners for the buttons
    document.getElementById(`submit-answer-${this.uniqueId}`).addEventListener('click', () => this.submitAnswer());
    document.getElementById(`prev-question-${this.uniqueId}`).addEventListener('click', () => this.goToPreviousQuestion());
    document.getElementById(`next-question-${this.uniqueId}`).addEventListener('click', () => this.goToNextQuestion());
  }

  showQuestion() {
    // If we moved beyond the virtual completion card, clamp back
    if (this.currentQuestionIndex > this.totalQuestions) {
      this.currentQuestionIndex = this.totalQuestions;
    }

    // Update the question counter (hide count on completion card)
    const counter = document.getElementById(`question-counter-${this.uniqueId}`);
    if (this.currentQuestionIndex === this.totalQuestions) {
      counter.textContent = '';
    } else {
      counter.textContent = `Spørsmål ${this.currentQuestionIndex + 1} / ${this.totalQuestions}`;
    }

    // Clear the question container before rendering the new question
    const questionContainer = document.getElementById(`question-container-${this.uniqueId}`);
    questionContainer.innerHTML = ''; // Clear previous question

    // If we are on the virtual completion card, show the completion banner
    // and do NOT render a question (buttons remain for navigation)
    const banner = document.getElementById(`quiz-completion-${this.uniqueId}`);
    if (this.currentQuestionIndex === this.totalQuestions) {
      if (banner) banner.style.display = 'block';
      this.updateNavigationButtons();
      return;
    } else if (banner) {
      banner.style.display = 'none';
    }

    const questionData = this.questionsData[this.currentQuestionIndex];
    if (!questionData) {
      return; // Nothing to show
    }

    // Check if we already have an instance of the question
    if (Object.prototype.hasOwnProperty.call(this.questionInstances, this.currentQuestionIndex)) {
      // Retrieve the existing instance
      this.currentQuestion = this.questionInstances[this.currentQuestionIndex];
    } else {
      // Create a new instance and store it
      this.currentQuestion = new MultipleChoiceQuestion(questionData);
      // Shuffle the answers on first creation
      this.currentQuestion.shuffleAnswers();
      this.questionInstances[this.currentQuestionIndex] = this.currentQuestion;
    }

    // Render the question
    this.currentQuestion.render(`question-container-${this.uniqueId}`);

    // Update navigation buttons and other UI elements
    this.updateNavigationButtons();
  }

  submitAnswer() {
    // Disable the submit button to prevent multiple clicks
    const submitButton = document.getElementById(`submit-answer-${this.uniqueId}`);
    submitButton.disabled = true;

    const isCorrect = this.currentQuestion.checkAnswers(false); // Pass 'false' to suppress alerts

    if (isCorrect) {
      this.correctlyAnsweredQuestions.add(this.currentQuestionIndex); // Track correct answer
      this.showToast('success');
      // Mark the question as correctly answered
      this.currentQuestion.markAsCorrectlyAnswered();
      // Update navigation buttons after a short delay
      setTimeout(() => {
        this.updateNavigationButtons();
      }, 800); // Delay to allow the user to see the feedback
    } else {
      this.showToast('error');
      // Re-enable the submit button so the user can try again
      setTimeout(() => {
        submitButton.disabled = false;
      }, 1500); // Match the toast display time
    }
  }

  showToast(type) {
    const toastId = type === 'success' ? `toast-success-${this.uniqueId}` : `toast-error-${this.uniqueId}`;
    const toast = document.getElementById(toastId);

    if (!toast) {
      console.error(`Toast element with ID ${toastId} not found.`);
      return;
    }

    // Ensure the container is positioned relatively
    if (getComputedStyle(this.container).position === 'static') {
      this.container.style.position = 'relative';
    }

    // Display the toast in the center of the container
    toast.style.position = 'absolute';
    toast.style.top = '50%';
    toast.style.left = '50%';
    toast.style.transform = 'translate(-50%, -50%)';
    toast.style.display = 'block';

    // Hide the toast after a delay
    setTimeout(() => {
      toast.style.display = 'none';
    }, 1500); // Display for 1.5 seconds
  }

  finishQuiz() {
    // Mark finished and show completion banner, keep UI for navigation
    this.isFinished = true;
    const banner = document.getElementById(`quiz-completion-${this.uniqueId}`);
    if (banner) {
      banner.style.display = 'block';
    }
  }

  updateNavigationButtons() {
    const prevButton = document.getElementById(`prev-question-${this.uniqueId}`);
    const nextButton = document.getElementById(`next-question-${this.uniqueId}`);
    const submitButton = document.getElementById(`submit-answer-${this.uniqueId}`);

    const currentIndex = this.currentQuestionIndex;

    // Show or hide the Previous button
    if (currentIndex === 0 || !this.correctlyAnsweredQuestions.has(currentIndex - 1)) {
      prevButton.style.display = 'none'; // Hide the button
    } else {
      prevButton.style.display = ''; // Show the button
    }

    // Show or hide the Next button
    if (currentIndex === this.totalQuestions) {
      nextButton.style.display = 'none'; // No next beyond completion card
    } else if (this.correctlyAnsweredQuestions.has(currentIndex)) {
      nextButton.style.display = ''; // Show the button (including on last real question)
    } else {
      nextButton.style.display = 'none'; // Hide the button
    }

    // Disable/hide the submit button on completion card; otherwise disable if already correct
    if (currentIndex === this.totalQuestions) {
      submitButton.style.display = 'none';
    } else {
      submitButton.style.display = '';
      submitButton.disabled = this.correctlyAnsweredQuestions.has(currentIndex);
    }
  }

  goToPreviousQuestion() {
    if (this.currentQuestionIndex > 0 && this.correctlyAnsweredQuestions.has(this.currentQuestionIndex - 1)) {
      this.currentQuestionIndex--;
      this.showQuestion();
      // this.scrollToQuizContainer(); // Scroll to the quiz container
    }
  }

  goToNextQuestion() {
    if (this.currentQuestionIndex === this.totalQuestions) {
      return; // Already at completion card
    }
    if (this.correctlyAnsweredQuestions.has(this.currentQuestionIndex)) {
      if (this.currentQuestionIndex < this.totalQuestions - 1) {
        this.currentQuestionIndex++;
        this.showQuestion();
      } else if (this.currentQuestionIndex === this.totalQuestions - 1) {
        // Move to virtual completion card
        this.currentQuestionIndex = this.totalQuestions;
        this.finishQuiz();
        this.showQuestion();
      }
      // this.scrollToQuizContainer(); // Scroll to the quiz container
    }
  }

  scrollToQuizContainer() {
    this.container.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
      inline: 'nearest',
    });
  }
}

// Expose globally (for inline scripts)
window.SequentialMultipleChoiceQuiz = SequentialMultipleChoiceQuiz;
window.MultipleChoiceQuestion = MultipleChoiceQuestion;
