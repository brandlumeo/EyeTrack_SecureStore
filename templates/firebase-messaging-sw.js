importScripts('https://www.gstatic.com/firebasejs/10.9.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.9.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyAKwZKDrKpqebF8dTLOIya9cngXXHbgTCA",
  authDomain: "eyetrack-store.firebaseapp.com",
  projectId: "eyetrack-store",
  storageBucket: "eyetrack-store.firebasestorage.app",
  messagingSenderId: "1045611196441",
  appId: "1:1045611196441:web:e9c3fc51989a9c682a3a88",
  measurementId: "G-VWS0E9RDQD"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification?.title || 'New Notification';
  const notificationOptions = {
    body: payload.notification?.body || '',
    icon: '/static/image/logo.png'
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
