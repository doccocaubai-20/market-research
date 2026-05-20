import axios from 'axios';

const BASE_URL = 'http://localhost:8080/api';

export const runResearch = async (topic) => {
    const response = await axios.post(`${BASE_URL}/research`, { topic });
    return response.data;
};

export const streamResearch = (topic) => {
    const url = `${BASE_URL}/research/stream?topic=${encodeURIComponent(topic)}`;
    return new EventSource(url);
};

export const getHistory = async () => {
    const response = await axios.get(`${BASE_URL}/history`);
    return response.data;
};

export const getReportById = async (id) => {
    const response = await axios.get(`${BASE_URL}/history/${id}`);
    return response.data;
};

export const deleteReport = async (id) => {
    const response = await axios.delete(`${BASE_URL}/history/${id}`);
    return response.data;
};