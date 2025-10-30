import { useState, useRef, useEffect } from 'react';
import { Box, Typography, Alert, createTheme, ThemeProvider, CircularProgress } from '@mui/material';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import type { QueryResponse, ChatMessage as ChatMessageType } from './types';
import './App.css';

function App() {
	const [messages, setMessages] = useState<ChatMessageType[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	const theme = createTheme({
		palette: {
			mode: 'dark',
		},
	});

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	const handleQuery = async (question: string) => {
		const userMessage: ChatMessageType = {
			id: Date.now().toString(),
			type: 'user',
			question,
			timestamp: new Date(),
		};
		setMessages((prev) => [...prev, userMessage]);
		setLoading(true);
		setError(null);

		try {
			const response = await fetch('http://localhost:8000/ask', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ question }),
			});
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			const data: QueryResponse = await response.json();
			const assistantMessage: ChatMessageType = {
				id: (Date.now() + 1).toString(),
				type: 'assistant',
				question,
				query: data.query,
				response: data.response,
				timestamp: new Date(),
			};
			setMessages((prev) => [...prev, assistantMessage]);
		} catch (err) {
			setError(err instanceof Error ? err.message : 'An error occurred');
		} finally {
			setLoading(false);
		}
	};

	return (
		<ThemeProvider theme={theme}>
			<Box
				sx={{
					display: 'flex',
					flexDirection: 'column',
					height: '100vh',
					background: 'linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%)',
				}}
			>
				<Box
					p={3}
					display="flex"
					flexDirection="column"
					alignItems="center"
					gap={1}
					sx={{
						color: 'white',
						borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
						boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
					}}
				>
					<Typography
						variant="h4"
						sx={{
							fontWeight: 800,
						}}
					>
						AskDB
					</Typography>
					<Typography variant="body2">Ask questions about your database in natural language</Typography>
				</Box>

				<Box
					display="flex"
					flexDirection="column"
					flex={1}
					alignItems="center"
					sx={{
						overflowY: 'auto',
					}}
				>
					<Box display="flex" flexDirection="column" p={2} width="100%" flex={1} maxWidth="950px">
						<Box
							display="flex"
							flexDirection="column"
							flex={1}
							pt={2}
							pb={2}
							sx={{
								overflowY: 'auto',
								scrollBehavior: 'smooth',
							}}
						>
							{messages.length === 0 ? (
								<Box
									display="flex"
									flexDirection="column"
									alignItems="center"
									justifyContent="center"
									height="100%"
									color="#e0e0e0"
									gap={1}
								>
									<Typography variant="h4" fontWeight={800}>
										Welcome to AskDB
									</Typography>
									<Typography variant="body1">
										Start by asking a question about your database
									</Typography>
								</Box>
							) : (
								messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
							)}
							{error && (
								<Alert
									severity="error"
									sx={{
										background:
											'linear-gradient(135deg, rgba(255, 100, 100, 0.15) 0%, rgba(255, 150, 100, 0.1) 100%)',
										border: '1.5px solid rgba(255, 100, 100, 0.4)',
										borderRadius: '12px',
										color: '#ff6464',
									}}
								>
									<strong>Error:</strong> {error}
								</Alert>
							)}
							{loading && (
								<Box
									display="flex"
									justifyContent="center"
									alignItems="center"
									py={3}
								>
									<CircularProgress sx={{ color: '#667eea' }} />
								</Box>
							)}
							<Box ref={messagesEndRef} />
						</Box>
					</Box>
				</Box>
				<ChatInput onSubmit={handleQuery} loading={loading} />
			</Box>
		</ThemeProvider>
	);
}

export default App;
