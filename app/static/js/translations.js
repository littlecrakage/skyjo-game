// Language translations for Skyjo
var TRANSLATIONS = {
    en: {
        // Common
        back: "← Back",
        copy: "Copy",
        copied: "Copied!",
        cancel: "Cancel",
        loading: "Loading...",
        
        // Home page
        home_title: "Skyjo",
        home_subtitle: "The card game",
        create_game: "Create Game",
        join_game: "Join Game",
        public_lobbies: "Public Lobbies",
        footer_text: "Built with Flask & SocketIO",
        
        // Create page
        create_title: "Create Game",
        your_name: "Your Name",
        enter_name: "Enter your name",
        max_players: "Max Players",
        players: "Players",
        turn_timer: "Turn Timer (seconds)",
        unlimited_time: "Set to 0 for unlimited time",
        public_game: "Public game (visible in lobby list)",
        finish_round: "Finish round when a player reveals all cards",
        create_btn: "Create Game",
        
        // Join page
        join_title: "Join Game",
        game_code: "Game Code",
        enter_code: "Enter 6-character code",
        join_btn: "Join Game",
        or: "or",
        browse_public: "Browse Public Games",
        
        // Lobbies page
        lobbies_title: "Public Lobbies",
        no_games: "No public games available",
        check_back: "Create one or check back later!",
        create_new: "Create New Game",
        join: "Join",
        no_timer: "No timer",
        turns: "turns",
        
        // Room page
        room: "Room",
        players_count: "Players",
        spectating: "👁 Spectating",
        host: "Host",
        you: "(You)",
        disconnected: "Disconnected",
        settings: "Settings",
        turn_timer_label: "Turn Timer",
        end_condition: "End Condition",
        finish_round_opt: "Finish round",
        stop_immediately: "Stop immediately",
        visibility: "Visibility",
        public: "Public",
        private: "Private",
        host_controls: "Host Controls",
        add_bot: "Add Bot",
        start_game: "Start Game",
        need_players: "Need at least 2 players to start",
        waiting_host: "Waiting for the host to start the game...",
        invite_friends: "Invite Friends",
        
        // Bot modal
        select_difficulty: "Select Bot Difficulty",
        easy: "Easy",
        medium: "Medium",
        hard: "Hard",
        random_choices: "Random choices",
        smart_decisions: "Smart decisions",
        card_counting: "Card counting",
        
        // Playing page
        round: "Round",
        draw: "Draw",
        discard: "Discard",
        your_card: "Your card:",
        discard_reveal: "Discard & Reveal",
        reveal_cards: "Reveal 2 Cards",
        click_reveal: "Click 2 cards to reveal",
        your_turn: "Your turn!",
        draw_card: "Draw from deck or take discard",
        place_or_discard: "Place card or discard & reveal",
        waiting_turn: "Waiting for",
        round_over: "Round Over!",
        game_over: "Game Over!",
        winner: "Winner",
        next_round: "Next Round",
        back_home: "Back to Home",
        final_scores: "Final Scores",
        
        // Notifications
        joined_game: "joined the game",
        left_game: "left the game",
        reconnected: "reconnected",
        connection_lost: "Connection lost. Reconnecting...",
        game_starting: "Game is starting!",
        timed_out: "timed out - auto action!",
        
        // Game Log
        game_log: "Game Log",
        drew_from: "drew from",
        placed_card: "placed a card",
        revealed_card: "revealed a card",
        discarded_card: "discarded",
        eliminated_column: "eliminated a column!",
        turn_of: "Turn:",
        
        // Scores
        round_score: "Round",
        total_score: "Total",
        spectator: "Spectator"
    },
    fr: {
        // Common
        back: "← Retour",
        copy: "Copier",
        copied: "Copié !",
        cancel: "Annuler",
        loading: "Chargement...",
        
        // Home page
        home_title: "Skyjo",
        home_subtitle: "Le jeu de cartes",
        create_game: "Créer une partie",
        join_game: "Rejoindre",
        public_lobbies: "Parties publiques",
        footer_text: "Créé avec Flask & SocketIO",
        
        // Create page
        create_title: "Créer une partie",
        your_name: "Votre nom",
        enter_name: "Entrez votre nom",
        max_players: "Joueurs max",
        players: "Joueurs",
        turn_timer: "Temps par tour (secondes)",
        unlimited_time: "Mettre 0 pour temps illimité",
        public_game: "Partie publique (visible dans la liste)",
        finish_round: "Terminer le tour quand un joueur révèle toutes ses cartes",
        create_btn: "Créer la partie",
        
        // Join page
        join_title: "Rejoindre une partie",
        game_code: "Code de la partie",
        enter_code: "Entrez le code à 6 caractères",
        join_btn: "Rejoindre",
        or: "ou",
        browse_public: "Parcourir les parties publiques",
        
        // Lobbies page
        lobbies_title: "Parties publiques",
        no_games: "Aucune partie disponible",
        check_back: "Créez-en une ou revenez plus tard !",
        create_new: "Créer une partie",
        join: "Rejoindre",
        no_timer: "Sans limite",
        turns: "par tour",
        
        // Room page
        room: "Salle",
        players_count: "Joueurs",
        spectating: "👁 Spectateur",
        host: "Hôte",
        you: "(Vous)",
        disconnected: "Déconnecté",
        settings: "Paramètres",
        turn_timer_label: "Temps par tour",
        end_condition: "Fin de manche",
        finish_round_opt: "Terminer la manche",
        stop_immediately: "Arrêt immédiat",
        visibility: "Visibilité",
        public: "Publique",
        private: "Privée",
        host_controls: "Contrôles hôte",
        add_bot: "Ajouter un bot",
        start_game: "Démarrer",
        need_players: "Il faut au moins 2 joueurs pour commencer",
        waiting_host: "En attente du lancement par l'hôte...",
        invite_friends: "Inviter des amis",
        
        // Bot modal
        select_difficulty: "Choisir la difficulté du bot",
        easy: "Facile",
        medium: "Moyen",
        hard: "Difficile",
        random_choices: "Choix aléatoires",
        smart_decisions: "Décisions intelligentes",
        card_counting: "Compte les cartes",
        
        // Playing page
        round: "Manche",
        draw: "Pioche",
        discard: "Défausse",
        your_card: "Votre carte :",
        discard_reveal: "Défausser & Révéler",
        reveal_cards: "Révélez 2 cartes",
        click_reveal: "Cliquez sur 2 cartes pour les révéler",
        your_turn: "À vous de jouer !",
        draw_card: "Piochez ou prenez la défausse",
        place_or_discard: "Placez la carte ou défaussez & révélez",
        waiting_turn: "En attente de",
        round_over: "Fin de manche !",
        game_over: "Partie terminée !",
        winner: "Gagnant",
        next_round: "Manche suivante",
        back_home: "Retour à l'accueil",
        final_scores: "Scores finaux",
        
        // Notifications
        joined_game: "a rejoint la partie",
        left_game: "a quitté la partie",
        reconnected: "s'est reconnecté",
        connection_lost: "Connexion perdue. Reconnexion...",
        game_starting: "La partie commence !",
        timed_out: "temps écoulé - action auto !",
        
        // Game Log
        game_log: "Journal de jeu",
        drew_from: "a pioché de",
        placed_card: "a placé une carte",
        revealed_card: "a révélé une carte",
        discarded_card: "a défaussé",
        eliminated_column: "a éliminé une colonne !",
        turn_of: "Tour de",
        
        // Scores
        round_score: "Manche",
        total_score: "Total",
        spectator: "Spectateur"
    }
};

// Get current language from localStorage or default to 'en'
function getCurrentLang() {
    return localStorage.getItem('skyjo_lang') || 'en';
}

// Set language
function setLang(lang) {
    localStorage.setItem('skyjo_lang', lang);
    applyTranslations();
    updateLangButton();
}

// Toggle language
function toggleLang() {
    var current = getCurrentLang();
    setLang(current === 'en' ? 'fr' : 'en');
}

// Get translation
function t(key) {
    var lang = getCurrentLang();
    return TRANSLATIONS[lang][key] || TRANSLATIONS['en'][key] || key;
}

// Update language button display
function updateLangButton() {
    var btn = document.getElementById('lang-btn');
    if (btn) {
        var current = getCurrentLang();
        btn.textContent = current === 'en' ? '🇫🇷 FR' : '🇬🇧 EN';
    }
}

// Apply translations to elements with data-i18n attribute
function applyTranslations() {
    var elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(function(el) {
        var key = el.getAttribute('data-i18n');
        if (el.tagName === 'INPUT' && el.placeholder) {
            el.placeholder = t(key);
        } else {
            el.textContent = t(key);
        }
    });
    
    // Update HTML lang attribute
    document.documentElement.lang = getCurrentLang();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateLangButton();
    applyTranslations();
});
