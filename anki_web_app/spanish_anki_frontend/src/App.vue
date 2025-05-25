<template>
  <nav>
    <router-link to="/">Flashcards</router-link> | 
    <router-link to="/dashboard">Dashboard</router-link> | 
    <router-link to="/sentences">Sentences</router-link>
    <!-- Link to SentenceDetailView will typically be from within SentenceListView -->
  </nav>
  <router-view/>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;
  display: flex;
  flex-wrap: wrap; /* Allow items to wrap to the next line */
  justify-content: center; /* Center items for a cleaner look when wrapped */
  gap: 10px; /* Add some space between nav items */
}

nav a {
  font-weight: bold;
  color: #2c3e50;
  padding: 5px 10px; /* Add some padding for easier tapping */
  text-decoration: none; /* Remove underline by default */
  border-radius: 4px; /* Slightly rounded corners for a modern look */
}

nav a.router-link-exact-active {
  color: #ffffff;
  background-color: #42b983; /* Highlight active link with background color */
}

/* Media Query for smaller screens */
@media (max-width: 600px) {
  nav {
    padding: 15px;
    flex-direction: column; /* Stack items vertically */
    align-items: center; /* Center items when stacked */
  }

  nav a {
    padding: 8px 15px; /* Adjust padding for vertical layout */
    width: 80%; /* Make links take more width for easier tapping */
    text-align: center; /* Center text within the link */
    margin-bottom: 5px; /* Add margin between stacked links */
  }
}
</style>
