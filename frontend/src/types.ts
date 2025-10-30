export interface QueryResponse {
	query?: string;
	response: string;
}

export interface QueryRequest {
	question: string;
}

export interface ChatMessage {
	id: string;
	type: 'user' | 'assistant';
	question: string;
	query?: string;
	response?: string;
	timestamp: Date;
}
