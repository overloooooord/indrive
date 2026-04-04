'use strict';
const API_BASE = '/api';
async function apiRequest(method, endpoint, body = null) {
  const options = {
    method: method,
    headers: {
      'Content-Type': 'application/json',
    },
  };
  if (body && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(body);
  }
  const url = `${API_BASE}${endpoint}`;
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data.detail
        || data.error
        || JSON.stringify(data)
        || `Ошибка ${response.status}`;
      throw new Error(errorMsg);
    }
    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Нет связи с сервером. Проверьте подключение.');
    }
    throw error;
  }
}
const API = {
  getCities: () => apiRequest('GET', '/cities/'),
  getRegion: (city) => apiRequest('GET', `/cities/${encodeURIComponent(city)}/regions/`),
  submitApplication: (data) => apiRequest('POST', '/applications/', data),
  submitMBTI: (applicationId, answers) =>
    apiRequest('POST', '/tests/mbti/', {
      application_id: applicationId,
      answers: answers,
    }),
  submitLanguageTest: (data) =>
    apiRequest('POST', '/tests/language/', data),
};
